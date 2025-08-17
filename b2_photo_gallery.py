#!/usr/bin/env python3

import os
import sys
import argparse
from datetime import datetime
import b2sdk.v2 as b2
from b2sdk._internal.exception import FileNotPresent
import mimetypes
from pathlib import Path
import re
import hashlib
import json
import subprocess
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS, GPSTAGS
import logging
from typing import List, Dict, Optional, Tuple, Any
import textwrap
import tempfile
import shutil
import multiprocessing
from functools import partial
from layout_strategies import LayoutStrategy, SmartLayoutStrategy

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_b2_credentials() -> Dict[str, str]:
    """Get B2 credentials from b2 CLI tool"""
    try:
        result = subprocess.run(['b2', 'account', 'get'], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("Failed to get B2 credentials")
        
        account_info = json.loads(result.stdout)
        return {
            'key_id': account_info['applicationKeyId'],
            'app_key': account_info['applicationKey'],
            'bucket': 'motovids'  # Using the same bucket as before
        }
    except Exception as e:
        logger.error(f"Error getting B2 credentials: {e}")
        sys.exit(1)

def generate_title_from_path(path: str) -> str:
    """Generate a title from the directory path"""
    # Get the last directory name
    dir_name = os.path.basename(os.path.normpath(path))
    
    # Convert to title case and replace underscores with spaces
    title = dir_name.replace('_', ' ').title()
    
    return title

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA1 hash of a file"""
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        # Read the file in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b''):
            sha1.update(chunk)
    return sha1.hexdigest()

def extract_image_metadata(file_path: str) -> Dict[str, Any]:
    """Extract comprehensive metadata from an image file"""
    metadata = {
        "dimensions": {"width": 0, "height": 0, "aspect_ratio": 0.0},
        "file_info": {"size_bytes": 0, "format": "", "color_mode": ""},
        "exif": {},
        "layout_hints": {
            "is_portrait": False,
            "is_panoramic": False,
            "suggested_grid_span": 1,
            "visual_weight": "medium"
        }
    }
    
    try:
        # Get file size
        metadata["file_info"]["size_bytes"] = os.path.getsize(file_path)
        
        with Image.open(file_path) as img:
            # Basic image info
            metadata["file_info"]["format"] = img.format or "UNKNOWN"
            metadata["file_info"]["color_mode"] = img.mode
            
            # Get dimensions with EXIF orientation applied
            img = ImageOps.exif_transpose(img)
            width, height = img.size
            metadata["dimensions"]["width"] = width
            metadata["dimensions"]["height"] = height
            metadata["dimensions"]["aspect_ratio"] = round(width / height, 2) if height > 0 else 0.0
            
            # Extract EXIF data
            if hasattr(img, '_getexif') and img._getexif() is not None:
                exif_data = img._getexif()
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    
                    # Convert complex EXIF values to strings
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8')
                        except UnicodeDecodeError:
                            value = str(value)
                    elif isinstance(value, tuple) and len(value) == 2:
                        # Handle rational numbers (like focal length)
                        if value[1] != 0:
                            value = round(value[0] / value[1], 2)
                        else:
                            value = value[0]
                    
                    metadata["exif"][tag] = value
                    
                    # Extract GPS coordinates if available
                    if tag == "GPSInfo" and isinstance(value, dict):
                        gps_coords = extract_gps_coordinates(value)
                        if gps_coords:
                            metadata["exif"]["gps_coordinates"] = gps_coords
            
            # Calculate layout hints
            aspect_ratio = metadata["dimensions"]["aspect_ratio"]
            metadata["layout_hints"]["is_portrait"] = aspect_ratio < 1.0
            metadata["layout_hints"]["is_panoramic"] = aspect_ratio > 2.5
            
            # Suggest grid span based on image characteristics
            if metadata["layout_hints"]["is_panoramic"]:
                metadata["layout_hints"]["suggested_grid_span"] = 3  # Full width
                metadata["layout_hints"]["visual_weight"] = "high"
            elif metadata["layout_hints"]["is_portrait"]:
                metadata["layout_hints"]["suggested_grid_span"] = 1
                metadata["layout_hints"]["visual_weight"] = "medium"
            elif aspect_ratio > 1.5:
                metadata["layout_hints"]["suggested_grid_span"] = 2
                metadata["layout_hints"]["visual_weight"] = "medium"
            else:
                metadata["layout_hints"]["suggested_grid_span"] = 1
                metadata["layout_hints"]["visual_weight"] = "medium"
                
    except Exception as e:
        logger.warning(f"Could not extract metadata for {file_path}: {e}")
    
    return metadata

def extract_gps_coordinates(gps_info: Dict) -> Optional[List[float]]:
    """Extract GPS coordinates from EXIF GPS info"""
    try:
        lat_ref = gps_info.get(1)  # N or S
        lat = gps_info.get(2)  # Latitude
        lon_ref = gps_info.get(3)  # E or W  
        lon = gps_info.get(4)  # Longitude
        
        if lat and lon:
            # Convert from degrees, minutes, seconds to decimal
            lat_decimal = convert_to_degrees(lat)
            lon_decimal = convert_to_degrees(lon)
            
            # Apply hemisphere
            if lat_ref == 'S':
                lat_decimal = -lat_decimal
            if lon_ref == 'W':
                lon_decimal = -lon_decimal
                
            return [round(lat_decimal, 6), round(lon_decimal, 6)]
    except Exception:
        pass
    return None

def convert_to_degrees(value):
    """Convert GPS coordinates from degrees, minutes, seconds to decimal degrees"""
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        degrees = float(value[0])
        minutes = float(value[1]) / 60.0
        seconds = float(value[2]) / 3600.0
        return degrees + minutes + seconds
    return float(value)

def get_image_dimensions(file_path: str) -> tuple:
    """Get image dimensions using PIL, honoring EXIF orientation (legacy compatibility)"""
    metadata = extract_image_metadata(file_path)
    return (metadata["dimensions"]["width"], metadata["dimensions"]["height"])

def get_metadata_cache_path(output_path: str) -> str:
    """Get the path for the metadata cache file"""
    output_dir = os.path.dirname(output_path)
    output_filename = os.path.splitext(os.path.basename(output_path))[0]
    return os.path.join(output_dir, f"{output_filename}_metadata.json")

def load_metadata_cache(cache_path: str) -> Dict[str, Any]:
    """Load metadata cache from JSON file"""
    try:
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load metadata cache from {cache_path}: {e}")
    
    return {"gallery_metadata": {}, "images": {}}

def save_metadata_cache(cache_path: str, metadata: Dict[str, Any]) -> None:
    """Save metadata cache to JSON file"""
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        logger.debug(f"Saved metadata cache to {cache_path}")
    except Exception as e:
        logger.error(f"Could not save metadata cache to {cache_path}: {e}")

def is_metadata_stale(image_path: str, cached_metadata: Dict[str, Any]) -> bool:
    """Check if cached metadata is stale compared to the actual file"""
    try:
        file_mtime = os.path.getmtime(image_path)
        file_size = os.path.getsize(image_path)
        
        cached_mtime = cached_metadata.get("file_info", {}).get("modified_time", 0)
        cached_size = cached_metadata.get("file_info", {}).get("size_bytes", 0)
        
        return file_mtime != cached_mtime or file_size != cached_size
    except Exception:
        return True

def update_metadata_cache(cache_data: Dict[str, Any], image_path: str, image_metadata: Dict[str, Any], urls: Dict[str, str]) -> None:
    """Update the metadata cache with new image data"""
    filename = os.path.basename(image_path)
    
    # Add file modification time for staleness checking
    try:
        image_metadata["file_info"]["modified_time"] = os.path.getmtime(image_path)
    except Exception:
        image_metadata["file_info"]["modified_time"] = 0
    
    # Add URLs to metadata
    image_metadata["urls"] = urls
    
    # Update cache
    cache_data["images"][filename] = image_metadata

def sanitize_filename(filename: str) -> str:
    """Convert filename to a safe format for URLs"""
    # Remove any non-alphanumeric characters except dots and dashes
    safe_name = re.sub(r'[^a-zA-Z0-9.-]', '_', filename)
    return safe_name

def get_b2_file_info(bucket, file_name: str) -> Optional[b2.FileVersion]:
    """Get file info from B2 if it exists"""
    try:
        file_info = bucket.get_file_info_by_name(file_name)
        return file_info
    except FileNotPresent:
        return None

def check_existing_images_in_b2(bucket, original_filename: str, destination_folder: str, local_path: str) -> Dict[str, Dict]:
    """Check which image sizes already exist in B2 and return their URLs"""
    existing_urls = {}
    
    # Calculate original image dimensions to determine what sizes would be generated
    try:
        with Image.open(local_path) as img:
            img = ImageOps.exif_transpose(img)
            original_width, original_height = img.size
            
            # Define target widths (same logic as process_image_for_responsive_loading)
            target_widths = []
            if original_width > 2000:
                target_widths = [2000, 1500, 1000]
            elif original_width > 1500:
                target_widths = [1500, 1000]
            elif original_width > 1000:
                target_widths = [1000]
            
            target_widths.append(original_width)
            target_widths = sorted(list(set(target_widths)))
            
            # Check if ALL sizes exist in B2
            all_sizes_exist = True
            for width in target_widths:
                size_key = f"{width}w"
                webp_name = f"{original_filename}_{width}w.webp"
                jpeg_name = f"{original_filename}_{width}w.jpeg"
                
                webp_path = f"{destination_folder}/{sanitize_filename(webp_name)}"
                jpeg_path = f"{destination_folder}/{sanitize_filename(jpeg_name)}"
                
                webp_exists = get_b2_file_info(bucket, webp_path)
                jpeg_exists = get_b2_file_info(bucket, jpeg_path)
                
                if webp_exists and jpeg_exists:
                    existing_urls[size_key] = {
                        'webp': f"https://f005.backblazeb2.com/file/{bucket.name}/{webp_path}",
                        'jpeg': f"https://f005.backblazeb2.com/file/{bucket.name}/{jpeg_path}"
                    }
                else:
                    all_sizes_exist = False
            
            # Only return URLs if ALL expected sizes exist
            if not all_sizes_exist:
                logger.debug(f"Not all sizes exist for {os.path.basename(local_path)}, will need to process")
                return {}
            else:
                logger.debug(f"All {len(existing_urls)} sizes exist for {os.path.basename(local_path)}")
                
    except Exception as e:
        logger.warning(f"Error checking existing images for {local_path}: {e}")
    
    return existing_urls

def upload_to_b2(local_path: str, bucket_name: str, b2_key_id: str, b2_app_key: str, destination_folder: str, force_reupload: bool = False) -> Dict[str, str]:
    """Upload a file to B2 and return the public URLs for all resolutions"""
    # Initialize B2 client
    info = b2.InMemoryAccountInfo()
    b2_api = b2.B2Api(info)
    b2_api.authorize_account("production", b2_key_id, b2_app_key)
    
    # Get bucket
    bucket = b2_api.get_bucket_by_name(bucket_name)
    
    # Get the original filename without extension
    original_filename = os.path.splitext(os.path.basename(local_path))[0]
    
    # Check if images already exist in B2 (unless force_reupload is True)
    if not force_reupload:
        existing_urls = check_existing_images_in_b2(bucket, original_filename, destination_folder, local_path)
        if existing_urls:
            logger.info(f"Found {len(existing_urls)} existing image sizes for {os.path.basename(local_path)}, skipping resize and upload")
            return existing_urls
    
    # Create a temporary directory for processed images
    with tempfile.TemporaryDirectory() as temp_dir:
        # Process image for responsive loading
        processed_images = process_image_for_responsive_loading(local_path, temp_dir)
        
        # Upload all versions and collect URLs
        urls = {}
        for size, formats in processed_images.items():
            if isinstance(formats, dict):
                # Handle WebP format URLs
                urls[size] = {}
                for format_type, format_path in formats.items():
                    # Create a unique filename for each resolution
                    file_name = f"{original_filename}_{size}.{format_type}"
                    safe_name = sanitize_filename(file_name)
                    destination_path = f"{destination_folder}/{safe_name}"
                    
                    # Check if file exists in B2
                    existing_file = get_b2_file_info(bucket, destination_path)
                    
                    if existing_file and not force_reupload:
                        logger.info(f"File {file_name} already exists in B2, skipping upload")
                        urls[size][format_type] = f"https://f005.backblazeb2.com/file/{bucket_name}/{destination_path}"
                    else:
                        # Calculate local file hash
                        local_hash = calculate_file_hash(format_path)
                        
                        if existing_file and existing_file.content_sha1 == local_hash and not force_reupload:
                            logger.info(f"File {file_name} already exists in B2 with matching hash, skipping upload")
                            urls[size][format_type] = f"https://f005.backblazeb2.com/file/{bucket_name}/{destination_path}"
                        else:
                            # Upload the file
                            uploaded_file = bucket.upload_local_file(
                                local_file=format_path,
                                file_name=destination_path
                            )
                            urls[size][format_type] = f"https://f005.backblazeb2.com/file/{bucket_name}/{destination_path}"
            else:
                # Handle single format URLs
                file_name = f"{original_filename}_{size}.jpg"
                safe_name = sanitize_filename(file_name)
                destination_path = f"{destination_folder}/{safe_name}"
                
                # Check if file exists in B2
                existing_file = get_b2_file_info(bucket, destination_path)
                
                if existing_file and not force_reupload:
                    logger.info(f"File {file_name} already exists in B2, skipping upload")
                    urls[size] = f"https://f005.backblazeb2.com/file/{bucket_name}/{destination_path}"
                else:
                    # Calculate local file hash
                    local_hash = calculate_file_hash(formats)
                    
                    if existing_file and existing_file.content_sha1 == local_hash and not force_reupload:
                        logger.info(f"File {file_name} already exists in B2 with matching hash, skipping upload")
                        urls[size] = f"https://f005.backblazeb2.com/file/{bucket_name}/{destination_path}"
                    else:
                        # Upload the file
                        uploaded_file = bucket.upload_local_file(
                            local_file=formats,
                            file_name=destination_path
                        )
                        urls[size] = f"https://f005.backblazeb2.com/file/{bucket_name}/{destination_path}"
    
    return urls

def generate_responsive_image_html(urls: Dict[str, str], alt_text: str, width: int, height: int, loading: str = "lazy", use_webp: bool = True) -> str:
    """Generate HTML for a responsive image with optional WebP support"""
    if use_webp and isinstance(next(iter(urls.values())), dict):
        # Handle WebP format URLs
        webp_srcset = []
        jpeg_srcset = []
        for size, format_urls in urls.items():
            width_value = int(size.replace('w', ''))
            webp_srcset.append(f"{format_urls['webp']} {width_value}w")
            jpeg_srcset.append(f"{format_urls['jpeg']} {width_value}w")
        
        return f"""<picture>
    <source type="image/webp" srcset="{', '.join(webp_srcset)}">
    <img src="{urls['1000w']['jpeg']}" 
         srcset="{', '.join(jpeg_srcset)}"
         alt="{alt_text}" 
         width="{width}" 
         height="{height}"
         loading="{loading}">
</picture>"""
    else:
        # Handle single format URLs
        srcset = []
        for size, url in urls.items():
            width_value = int(size.replace('w', ''))
            srcset.append(f"{url} {width_value}w")
        
        return f"""<img src="{urls['1000w']}" 
         srcset="{', '.join(srcset)}"
         alt="{alt_text}" 
         width="{width}" 
         height="{height}"
         loading="{loading}">"""


def generate_markdown(title: str, date: datetime, photos: List[Dict], output_file: str, layout_strategy: LayoutStrategy) -> None:
    """Generate a markdown file with the photos in the correct layout"""
    # Create the front matter
    front_matter = f"""---
layout: travel-post
title: "{title}"
date:   {date}
categories: travel
permalink: /travel/{date.strftime('%Y-%m-%d')}-{title.lower().replace(' ', '-')}.html
---

"""
    
    # Generate gallery HTML using the strategy
    gallery_html = layout_strategy.generate_gallery_html(photos, title)
    
    # Combine everything
    content = front_matter + gallery_html
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(content)

def get_available_strategies() -> Dict[str, LayoutStrategy]:
    """Get all available layout strategies"""
    return {
        'smart': SmartLayoutStrategy()
    }

def get_layout_strategy(strategy_name: str) -> LayoutStrategy:
    """Get layout strategy instance by name"""
    strategies = get_available_strategies()
    
    if strategy_name not in strategies:
        raise ValueError(f"Unknown layout strategy: {strategy_name}")
    
    return strategies[strategy_name]

def list_strategies() -> None:
    """List all available layout strategies with descriptions"""
    strategies = get_available_strategies()
    
    print("Available layout strategies:")
    print()
    
    for name, strategy in strategies.items():
        print(f"  {name:12} - {strategy.description}")
    
    print()

def parse_args():
    """Parse command line arguments with a better help message"""
    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""
        Upload photos to Backblaze B2 and generate Jekyll gallery pages.
        
        This tool will:
        1. Upload photos to your B2 bucket
        2. Generate a Jekyll markdown file with a gallery layout
        3. Skip already uploaded files (based on hash comparison)
        
        The generated gallery will have:
        - A full-width first image
        - Remaining images in a 3x3 grid layout
        - Proper image dimensions for better page loading
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'dir',
        nargs='?',
        help='Directory containing photos to upload'
    )
    
    parser.add_argument(
        '-t', '--title',
        help='Custom title for the gallery (defaults to directory name)'
    )
    
    parser.add_argument(
        '-d', '--date',
        help='Date for the post (YYYY-MM-DD format, defaults to today)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output markdown file path'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    parser.add_argument(
        '--force-reupload',
        action='store_true',
        help='Force reupload of images even if they already exist'
    )
    
    parser.add_argument(
        '--refresh-metadata',
        action='store_true',
        help='Force refresh of image metadata cache'
    )
    
    parser.add_argument(
        '--layout-strategy',
        default='smart',
        choices=list(get_available_strategies().keys()),
        help='Layout strategy to use for gallery arrangement (default: smart)'
    )
    
    parser.add_argument(
        '--list-strategies',
        action='store_true',
        help='List all available layout strategies and exit'
    )
    
    return parser.parse_args()

def process_single_image(args: Tuple[str, str, int]) -> Tuple[str, Dict[str, str]]:
    """Process a single image with a specific target width"""
    image_path, output_dir, width = args
    try:
        logger.info(f"Processing {os.path.basename(image_path)} at width {width}w")
        with Image.open(image_path) as img:
            # Normalize by EXIF orientation so pixels are upright
            img = ImageOps.exif_transpose(img)
            # Get original dimensions
            original_width, original_height = img.size
            logger.debug(f"Original dimensions: {original_width}x{original_height}")
            
            # Calculate new height maintaining aspect ratio
            ratio = width / original_width
            height = int(original_height * ratio)
            logger.debug(f"New dimensions: {width}x{height}")
            
            # Resize image
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Get the original filename without extension
            original_filename = os.path.splitext(os.path.basename(image_path))[0]
            
            # Create unique filenames for each resolution
            webp_path = os.path.join(output_dir, f"{original_filename}_{width}w.webp")
            jpeg_path = os.path.join(output_dir, f"{original_filename}_{width}w.jpg")
            
            # Save as WebP with high quality
            logger.debug(f"Saving WebP version: {os.path.basename(webp_path)}")
            resized.save(webp_path, "WEBP", quality=90, method=6)
            
            # Save as JPEG with high quality
            logger.debug(f"Saving JPEG version: {os.path.basename(jpeg_path)}")
            jpeg_img = resized
            if jpeg_img.mode in ("RGBA", "P"):
                jpeg_img = jpeg_img.convert("RGB")
            jpeg_img.save(jpeg_path, "JPEG", quality=95, optimize=True)
            
            logger.info(f"Completed processing {os.path.basename(image_path)} at width {width}w")
            return f"{width}w", {
                "webp": webp_path,
                "jpeg": jpeg_path
            }
    except Exception as e:
        logger.error(f"Error processing {image_path} at width {width}: {e}")
        return f"{width}w", {}

def process_image_for_responsive_loading(image_path: str, output_dir: str) -> Dict[str, str]:
    """
    Process an image to create multiple resolutions and WebP versions sequentially.
    Returns a dictionary of image URLs for different sizes.
    """
    try:
        logger.info(f"Starting responsive processing for {os.path.basename(image_path)}")
        with Image.open(image_path) as img:
            # Normalize by EXIF orientation so width/height reflect display
            img = ImageOps.exif_transpose(img)
            # Get original dimensions
            original_width, original_height = img.size
            logger.info(f"Image {os.path.basename(image_path)} dimensions: {original_width}x{original_height}")
            
            # Define target widths for different screen sizes
            target_widths = []
            if original_width > 2000:
                target_widths = [2000, 1500, 1000]
            elif original_width > 1500:
                target_widths = [1500, 1000]
            elif original_width > 1000:
                target_widths = [1000]
            
            # Always keep the original
            target_widths.append(original_width)
            
            # Remove duplicates and sort
            target_widths = sorted(list(set(target_widths)))
            logger.info(f"Will generate sizes: {target_widths}w for {os.path.basename(image_path)}")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Process each size sequentially
            processed_sizes = {}
            for width in target_widths:
                size_key, size_paths = process_single_image((image_path, output_dir, width))
                if size_paths:
                    processed_sizes[size_key] = size_paths
            
            logger.info(f"Successfully processed {len(processed_sizes)} sizes for {os.path.basename(image_path)}")
            return processed_sizes
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {e}")
        return {}

def process_images_parallel(image_paths: List[str], output_dir: str) -> List[Dict[str, str]]:
    """Process multiple images in parallel"""
    # Create a process pool with the number of CPU cores
    num_cores = multiprocessing.cpu_count()
    logger.info(f"Using {num_cores} CPU cores for parallel processing")
    logger.info(f"Processing {len(image_paths)} images in parallel")
    
    with multiprocessing.Pool(processes=num_cores) as pool:
        # Create a partial function with the output_dir fixed
        process_func = partial(process_image_for_responsive_loading, output_dir=output_dir)
        
        # Process all images in parallel
        results = pool.map(process_func, image_paths)
    
    # Log processing results
    successful = sum(1 for r in results if r)
    logger.info(f"Successfully processed {successful} out of {len(image_paths)} images")
    return results

def main():
    args = parse_args()
    
    # Handle list strategies option
    if args.list_strategies:
        list_strategies()
        sys.exit(0)
    
    # Validate directory is provided when not listing strategies
    if not args.dir:
        print("Error: Directory argument is required")
        sys.exit(1)
    
    # Set up logging with more detailed format
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get layout strategy
    layout_strategy = get_layout_strategy(args.layout_strategy)
    logger.info(f"Using layout strategy: {layout_strategy.name} - {layout_strategy.description}")
    
    # Validate directory exists
    if not os.path.isdir(args.dir):
        logger.error(f"Directory not found: {args.dir}")
        sys.exit(1)
    
    # Get B2 credentials
    logger.info("Getting B2 credentials...")
    credentials = get_b2_credentials()
    
    # Generate or use custom title
    title = args.title if args.title else generate_title_from_path(args.dir)
    logger.info(f"Using title: {title}")
    
    # Set default date if not provided
    if args.date:
        try:
            date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            logger.error("Invalid date format. Please use YYYY-MM-DD")
            sys.exit(1)
    else:
        date = datetime.now()
    
    # Set default output path if not provided
    if not args.output:
        args.output = f"_travel/{date.strftime('%Y-%m-%d')}-{title.lower().replace(' ', '-')}.markdown"
    
    # Set up metadata cache
    cache_path = get_metadata_cache_path(args.output)
    metadata_cache = load_metadata_cache(cache_path)
    
    # Update gallery metadata
    metadata_cache["gallery_metadata"] = {
        "title": title,
        "date": date.isoformat(),
        "total_images": 0  # Will be updated later
    }
    
    # Get list of image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
    photos = []
    
    # Sort files by name
    files = sorted(os.listdir(args.dir))
    
    if not files:
        logger.error(f"No files found in directory: {args.dir}")
        sys.exit(1)
    
    # Filter image files
    image_files = [os.path.join(args.dir, file) for file in files 
                  if os.path.splitext(file)[1].lower() in image_extensions]
    
    if not image_files:
        logger.error(f"No image files found in directory: {args.dir}")
        sys.exit(1)
    
    logger.info(f"Found {len(image_files)} image files to process")
    
    # Create a temporary directory for processed images
    with tempfile.TemporaryDirectory() as temp_dir:
        if args.dry_run:
            logger.info(f"Would process {len(image_files)} images")
            # Create dummy URLs for dry run with metadata
            for file in image_files:
                filename = os.path.basename(file)
                # Extract metadata for dry run to test layout logic
                cached_image_metadata = metadata_cache["images"].get(filename, {})
                if args.refresh_metadata or is_metadata_stale(file, cached_image_metadata) or not cached_image_metadata:
                    logger.info(f"Extracting metadata for dry run: {filename}")
                    image_metadata = extract_image_metadata(file)
                    update_metadata_cache(metadata_cache, file, image_metadata, {})
                else:
                    image_metadata = cached_image_metadata
                
                dummy_urls = {
                    '1000w': {'webp': f"https://example.com/{os.path.basename(file)}.webp", 
                             'jpeg': f"https://example.com/{os.path.basename(file)}.jpg"},
                    '2000w': {'webp': f"https://example.com/{os.path.basename(file)}.webp", 
                             'jpeg': f"https://example.com/{os.path.basename(file)}.jpg"}
                }
                photos.append({
                    'urls': dummy_urls,
                    'path': file,
                    'metadata': image_metadata
                })
        else:
            # Check for existing images first to avoid unnecessary processing
            logger.info("Checking for existing images in B2...")
            
            # Initialize B2 client for checking
            info = b2.InMemoryAccountInfo()
            b2_api = b2.B2Api(info)
            b2_api.authorize_account("production", credentials['key_id'], credentials['app_key'])
            bucket = b2_api.get_bucket_by_name(credentials['bucket'])
            
            files_to_process = []
            for file in image_files:
                filename = os.path.basename(file)
                original_filename = os.path.splitext(filename)[0]
                destination_folder = f"photos/{title.lower().replace(' ', '_')}"
                
                # Check if we have cached metadata and if it's still valid
                cached_image_metadata = metadata_cache["images"].get(filename, {})
                metadata_is_stale = is_metadata_stale(file, cached_image_metadata)
                
                # Extract metadata if needed
                if args.refresh_metadata or metadata_is_stale or not cached_image_metadata:
                    logger.info(f"Extracting metadata for {filename}")
                    image_metadata = extract_image_metadata(file)
                else:
                    logger.debug(f"Using cached metadata for {filename}")
                    image_metadata = cached_image_metadata
                
                # Check for existing URLs in B2 (unless force_reupload)
                if not args.force_reupload:
                    existing_urls = check_existing_images_in_b2(bucket, original_filename, destination_folder, file)
                    if existing_urls:
                        logger.info(f"All sizes already exist for {os.path.basename(file)}, skipping processing")
                        # Update metadata cache with existing URLs
                        update_metadata_cache(metadata_cache, file, image_metadata, existing_urls)
                        photos.append({
                            'urls': existing_urls,
                            'path': file,
                            'metadata': image_metadata
                        })
                        continue
                
                files_to_process.append((file, image_metadata))
            
            if files_to_process:
                logger.info(f"Processing {len(files_to_process)} new images...")
                # Extract just file paths for parallel processing
                file_paths = [item[0] for item in files_to_process]
                processed_results = process_images_parallel(file_paths, temp_dir)
                
                # Upload to B2 and collect results
                logger.info("Starting B2 uploads...")
                for (file, image_metadata), urls in zip(files_to_process, processed_results):
                    if urls:  # Only process if we have valid URLs
                        logger.info(f"Uploading {os.path.basename(file)} to B2...")
                        uploaded_urls = upload_to_b2(
                            file,
                            credentials['bucket'],
                            credentials['key_id'],
                            credentials['app_key'],
                            f"photos/{title.lower().replace(' ', '_')}",
                            args.force_reupload
                        )
                        
                        # Update metadata cache with new URLs
                        update_metadata_cache(metadata_cache, file, image_metadata, uploaded_urls)
                        
                        photos.append({
                            'urls': uploaded_urls,
                            'path': file,
                            'metadata': image_metadata
                        })
                        logger.info(f"Completed upload for {os.path.basename(file)}")
            else:
                logger.info("All images already exist in B2, no processing needed")
    
    if not photos:
        logger.error(f"No images were successfully processed")
        sys.exit(1)
    
    # Update final gallery metadata
    metadata_cache["gallery_metadata"]["total_images"] = len(photos)
    
    # Save metadata cache
    if not args.dry_run:
        save_metadata_cache(cache_path, metadata_cache)
        logger.info(f"Saved metadata cache to {cache_path}")
    
    # Generate markdown
    if not args.dry_run:
        logger.info(f"Generating markdown file: {args.output}")
        generate_markdown(title, date, photos, args.output, layout_strategy)
        logger.info("Done!")
    else:
        logger.info(f"Would generate markdown file: {args.output}")
        logger.info(f"Would save metadata cache to: {cache_path}")

if __name__ == '__main__':
    main() 
