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
from PIL import Image
import logging
from typing import List, Dict, Optional
import textwrap

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
    """Get image dimensions using PIL"""
    try:
        with Image.open(file_path) as img:
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

def upload_to_b2(local_path: str, bucket_name: str, b2_key_id: str, b2_app_key: str, destination_folder: str) -> str:
    """Upload a file to B2 and return the public URL"""
    # Initialize B2 client
    info = b2.InMemoryAccountInfo()
    b2_api = b2.B2Api(info)
    b2_api.authorize_account("production", b2_key_id, b2_app_key)
    
    # Get bucket
    bucket = b2_api.get_bucket_by_name(bucket_name)
    
    # Prepare file info
    file_name = os.path.basename(local_path)
    safe_name = sanitize_filename(file_name)
    destination_path = f"{destination_folder}/{safe_name}"
    
    # Calculate local file hash
    local_hash = calculate_file_hash(local_path)
    
    # Check if file exists in B2
    existing_file = get_b2_file_info(bucket, destination_path)
    
    if existing_file:
        # Compare hashes
        if existing_file.content_sha1 == local_hash:
            logger.info(f"File {file_name} already exists in B2 with matching hash, skipping upload")
            return f"https://f005.backblazeb2.com/file/{bucket_name}/{destination_path}"
        else:
            logger.info(f"File {file_name} exists in B2 but hash differs, uploading new version")
    else:
        logger.info(f"File {file_name} not found in B2, uploading")
    
    # Upload the file
    uploaded_file = bucket.upload_local_file(
        local_file=local_path,
        file_name=destination_path
    )
    
    # Get the public URL
    public_url = f"https://f005.backblazeb2.com/file/{bucket_name}/{destination_path}"
    return public_url

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
    
    # Create the gallery sections
    gallery_sections = []
    
    # Add a full-width first image if available
    if photos:
        first_photo = photos[0]
        width, height = get_image_dimensions(first_photo['path'])
        gallery_sections.append(f"""<div class="gallery">
    <div class="gallery-item full">
        <img src="{first_photo['url']}" alt="{title}" width="{width}" height="{height}">
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
        <img src="{photo['url']}" alt="{title}" width="{width}" height="{height}">
    </div>""")
            grid_html.append('</div>')
            gallery_sections.append('\n'.join(grid_html))
    
    # Combine everything
    content = front_matter + '\n\n'.join(gallery_sections)
    
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
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Validate directory exists
    if not os.path.isdir(args.dir):
        logger.error(f"Directory not found: {args.dir}")
        sys.exit(1)
    
    # Get B2 credentials
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
    
    for file in files:
        if os.path.splitext(file)[1].lower() in image_extensions:
            local_path = os.path.join(args.dir, file)
            
            if args.dry_run:
                logger.info(f"Would process {file}")
                photos.append({
                    'url': f"https://example.com/{file}",  # Placeholder URL
                    'path': local_path
                })
            else:
                # Upload to B2
                logger.info(f"Processing {file}...")
                url = upload_to_b2(
                    local_path,
                    credentials['bucket'],
                    credentials['key_id'],
                    credentials['app_key'],
                    f"photos/{title.lower().replace(' ', '_')}"
                )
                
                photos.append({
                    'url': url,
                    'path': local_path
                })
    
    if not photos:
        logger.error(f"No image files found in directory: {args.dir}")
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