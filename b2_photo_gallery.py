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
import logging
from typing import List, Dict, Optional, Tuple
import textwrap
import tempfile
import shutil
import multiprocessing
from functools import partial

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

def get_image_dimensions(file_path: str) -> tuple:
    """Get image dimensions using PIL, honoring EXIF orientation"""
    try:
        with Image.open(file_path) as img:
            img = ImageOps.exif_transpose(img)
            return img.size
    except Exception as e:
        logger.warning(f"Could not get dimensions for {file_path}: {e}")
        return (0, 0)

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

def upload_to_b2(local_path: str, bucket_name: str, b2_key_id: str, b2_app_key: str, destination_folder: str, force_reupload: bool = False) -> Dict[str, str]:
    """Upload a file to B2 and return the public URLs for all resolutions"""
    # Initialize B2 client
    info = b2.InMemoryAccountInfo()
    b2_api = b2.B2Api(info)
    b2_api.authorize_account("production", b2_key_id, b2_app_key)
    
    # Get bucket
    bucket = b2_api.get_bucket_by_name(bucket_name)
    
    # Create a temporary directory for processed images
    with tempfile.TemporaryDirectory() as temp_dir:
        # Get the original filename without extension
        original_filename = os.path.splitext(os.path.basename(local_path))[0]
        
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

def generate_gallery_html(photos: List[Dict], title: str) -> str:
    """Generate HTML for a photo gallery with a full-width first image and 3x3 grid for the rest"""
    gallery_sections = []
    
    # Add a full-width first image if available
    if photos:
        first_photo = photos[0]
        width, height = get_image_dimensions(first_photo['path'])
        
        gallery_sections.append(f"""<div class="gallery">
    <div class="gallery-item full">
        {generate_responsive_image_html(first_photo['urls'], title, width, height, loading="eager")}
    </div>
</div>""")
    
    # Group remaining photos into 3x3 grids
    remaining_photos = photos[1:] if photos else []
    while remaining_photos:
        grid_photos = remaining_photos[:9]
        remaining_photos = remaining_photos[9:]
        
        if grid_photos:
            grid_html = ['<div class="gallery grid-3x3">']
            for photo in grid_photos:
                width, height = get_image_dimensions(photo['path'])
                grid_html.append(f"""    <div class="gallery-item">
        {generate_responsive_image_html(photo['urls'], title, width, height)}
    </div>""")
            grid_html.append('</div>')
            gallery_sections.append('\n'.join(grid_html))
    
    return '\n\n'.join(gallery_sections)

def generate_markdown(title: str, date: datetime, photos: List[Dict], output_file: str) -> None:
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
    
    # Generate gallery HTML
    gallery_html = generate_gallery_html(photos, title)
    
    # Combine everything
    content = front_matter + gallery_html
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(content)

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
    
    # Set up logging with more detailed format
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
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
            # Create dummy URLs for dry run
            for file in image_files:
                dummy_urls = {
                    '1000w': {'webp': f"https://example.com/{os.path.basename(file)}.webp", 
                             'jpeg': f"https://example.com/{os.path.basename(file)}.jpg"},
                    '2000w': {'webp': f"https://example.com/{os.path.basename(file)}.webp", 
                             'jpeg': f"https://example.com/{os.path.basename(file)}.jpg"}
                }
                photos.append({
                    'urls': dummy_urls,
                    'path': file
                })
        else:
            # Process all images in parallel
            logger.info(f"Starting parallel processing of {len(image_files)} images...")
            processed_results = process_images_parallel(image_files, temp_dir)
            
            # Upload to B2 and collect results
            logger.info("Starting B2 uploads...")
            for file, urls in zip(image_files, processed_results):
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
                    
                    photos.append({
                        'urls': uploaded_urls,
                        'path': file
                    })
                    logger.info(f"Completed upload for {os.path.basename(file)}")
    
    if not photos:
        logger.error(f"No images were successfully processed")
        sys.exit(1)
    
    # Generate markdown
    if not args.dry_run:
        logger.info(f"Generating markdown file: {args.output}")
        generate_markdown(title, date, photos, args.output)
        logger.info("Done!")
    else:
        logger.info(f"Would generate markdown file: {args.output}")

if __name__ == '__main__':
    main() 
