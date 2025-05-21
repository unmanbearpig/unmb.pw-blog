#!/usr/bin/env python3

import os
import sys
import re
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
import requests
from PIL import Image
import argparse
import textwrap
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import threading
import gc
import psutil

# Import functions from b2-photo-gallery
from b2_photo_gallery import (
    get_b2_credentials,
    calculate_file_hash,
    process_image_for_responsive_loading,
    upload_to_b2,
    get_image_dimensions,
    generate_responsive_image_html
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global semaphore to limit concurrent image processing
processing_semaphore = threading.Semaphore(4)  # Limit to 4 concurrent image processing operations

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def download_image(url: str, temp_dir: str) -> Optional[str]:
    """Download an image and return the local path"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Get the filename from the URL
        filename = os.path.basename(url.split('?')[0])
        local_path = os.path.join(temp_dir, filename)
        
        # Save the file
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return local_path
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        return None

def extract_image_urls(content: str) -> Set[str]:
    """Extract image URLs from markdown content"""
    # Match both <img src="..."> and markdown ![alt](url) patterns
    img_pattern = r'(?:<img[^>]+src="([^"]+)"|!\[[^\]]*\]\(([^)]+)\))'
    matches = re.finditer(img_pattern, content)
    
    urls = set()
    for match in matches:
        url = match.group(1) or match.group(2)
        if url and url.startswith('http'):
            urls.add(url)
    
    return urls

def process_single_image(args: Tuple[str, str, Dict[str, str], str]) -> Optional[Tuple[str, str, Dict[str, str]]]:
    """Process a single image and return the old URL, new HTML, and processed URLs"""
    url, temp_dir, credentials, destination_folder = args
    try:
        # Acquire semaphore to limit concurrent processing
        with processing_semaphore:
            logger.info(f"Processing image: {url} (Memory usage: {get_memory_usage():.1f}MB)")
            
            # Download the image
            local_path = download_image(url, temp_dir)
            if not local_path:
                logger.error(f"Failed to download {url}")
                return None
            
            logger.debug(f"Downloaded to: {local_path}")
            
            # Get image dimensions
            width, height = get_image_dimensions(local_path)
            logger.debug(f"Image dimensions: {width}x{height}")
            
            # Process image for responsive loading
            logger.info(f"Processing image for responsive loading: {url}")
            processed_urls = process_image_for_responsive_loading(local_path, temp_dir)
            
            # Upload processed versions
            logger.info(f"Uploading to B2 folder: {destination_folder}")
            urls = upload_to_b2(
                local_path,
                credentials['bucket'],
                credentials['key_id'],
                credentials['app_key'],
                destination_folder
            )

            # Flatten urls if not using webp
            if not False:  # use_webp is always False here
                urls = {size: url['jpeg'] if isinstance(url, dict) and 'jpeg' in url else url for size, url in urls.items()}

            logger.debug(f"Generated URLs for sizes: {list(urls.keys())}")
            
            # Generate new HTML without WebP
            new_html = generate_responsive_image_html(
                urls,
                alt_text=Path(destination_folder).stem,
                width=width,
                height=height,
                use_webp=False  # Disable WebP
            )
            
            # Force garbage collection after processing each image
            gc.collect()
            
            return url, new_html, urls
    except Exception as e:
        logger.error(f"Error processing {url}: {e}")
        return None

def process_image_for_responsive_loading(image_path: str, output_dir: str) -> Dict[str, str]:
    """
    Process an image to create multiple resolutions without WebP versions.
    Returns a dictionary of image URLs for different sizes.
    """
    try:
        logger.info(f"Starting responsive processing for {os.path.basename(image_path)}")
        with Image.open(image_path) as img:
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
            
            # Prepare arguments for parallel processing
            process_args = [(image_path, output_dir, width) for width in target_widths]
            
            # Use multiprocessing to process images in parallel
            with multiprocessing.Pool() as pool:
                results = pool.map(process_single_size, process_args)
            
            # Convert results to dictionary and filter out any failed processing
            processed_sizes = {k: v for k, v in dict(results).items() if v}
            logger.info(f"Successfully processed {len(processed_sizes)} sizes for {os.path.basename(image_path)}")
            return processed_sizes
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {e}")
        return {}

def process_single_size(args: Tuple[str, str, int]) -> Tuple[str, str]:
    """Process a single image size without WebP"""
    image_path, output_dir, width = args
    try:
        with Image.open(image_path) as img:
            # Get original dimensions
            original_width, original_height = img.size
            
            # Calculate new height maintaining aspect ratio
            ratio = width / original_width
            height = int(original_height * ratio)
            
            # Resize image
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Get the original filename without extension
            original_filename = os.path.splitext(os.path.basename(image_path))[0]
            
            # Create unique filename for JPEG only
            jpeg_path = os.path.join(output_dir, f"{original_filename}_{width}w.jpg")
            
            # Save as JPEG with high quality
            resized.save(jpeg_path, "JPEG", quality=95, optimize=True)
            
            return f"{width}w", jpeg_path
    except Exception as e:
        logger.error(f"Error processing {image_path} at width {width}: {e}")
        return f"{width}w", ""

def update_markdown_file(file_path: str, credentials: Dict[str, str], max_concurrent: int, output_file: Optional[str] = None) -> None:
    """Update a markdown file with responsive images"""
    logger.info(f"Processing {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract image URLs
    image_urls = extract_image_urls(content)
    if not image_urls:
        logger.info(f"No images found in {file_path}")
        return
    
    logger.info(f"Found {len(image_urls)} images in {file_path}")
    
    # Create temporary directory for downloads
    with tempfile.TemporaryDirectory() as temp_dir:
        # Prepare arguments for parallel processing
        destination_folder = f"photos/{Path(file_path).stem}"
        process_args = [(url, temp_dir, credentials, destination_folder) for url in image_urls]
        
        logger.info(f"Using {max_concurrent} threads for processing")
        
        # Process images in parallel using ThreadPoolExecutor
        # Use the same max_concurrent limit for thread pool
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = [executor.submit(process_single_image, args) for args in process_args]
            
            # Process results as they complete
            for future in as_completed(futures):
                result = future.result()
                if result:
                    url, new_html, urls = result
                    # Replace old image tag with new responsive version using regex
                    # Match both <img src="url"> and ![alt](url) patterns
                    img_pattern = f'<img[^>]+src="{url}"[^>]*>'
                    markdown_pattern = f'!\\[[^\\]]*\\]\\({url}\\)'
                    
                    old_content = content
                    content = re.sub(img_pattern, new_html, content)
                    content = re.sub(markdown_pattern, new_html, content)
                    
                    if old_content == content:
                        logger.warning(f"Failed to replace image URL: {url}")
                    else:
                        logger.info(f"Successfully replaced image: {url}")
                
                # Log memory usage periodically
                logger.debug(f"Current memory usage: {get_memory_usage():.1f}MB")
    
    # Write updated content to output file or original file
    output_path = output_file or file_path
    with open(output_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Updated {output_path}")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""
        Update markdown files with responsive images.
        
        This tool will:
        1. Extract image URLs from markdown files
        2. Download and process images for responsive loading
        3. Upload processed images to B2
        4. Update markdown files with responsive image tags
        
        All operations are performed in parallel using the number of CPU cores
        for optimal performance.
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'file',
        help='Path to the markdown file to process'
    )
    
    parser.add_argument(
        '--output',
        help='Path to write the processed file (default: overwrite original file)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=None,
        help='Maximum number of concurrent operations (default: number of CPU cores)'
    )
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Set up logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Set up global semaphore with user-specified limit or CPU core count
    global processing_semaphore
    max_concurrent = args.max_concurrent or multiprocessing.cpu_count()
    processing_semaphore = threading.Semaphore(max_concurrent)
    logger.info(f"Using {max_concurrent} concurrent operations")
    
    # Get B2 credentials
    logger.info("Getting B2 credentials...")
    credentials = get_b2_credentials()
    
    # Process the file
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    if args.dry_run:
        logger.info(f"Would process {args.file}")
        return
    
    update_markdown_file(args.file, credentials, max_concurrent, args.output)
    logger.info("Done!")

if __name__ == '__main__':
    main() 