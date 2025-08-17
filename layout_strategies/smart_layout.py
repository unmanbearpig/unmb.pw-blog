from typing import List, Dict, Optional
from .base import LayoutStrategy


class SmartLayoutStrategy(LayoutStrategy):
    """Smart layout strategy that uses image metadata for optimal arrangement"""
    
    @property
    def name(self) -> str:
        return "smart"
    
    @property
    def description(self) -> str:
        return "Intelligent layout based on image metadata (aspect ratios, visual weight)"
    
    def select_hero_image(self, photos: List[Dict]) -> Optional[Dict]:
        """Select the best image for the hero/first position based on metadata"""
        if not photos:
            return None
        
        # Score images based on visual impact
        scored_photos = []
        for photo in photos:
            score = 0
            metadata = photo.get('metadata', {})
            layout_hints = metadata.get('layout_hints', {})
            dimensions = metadata.get('dimensions', {})
            
            # Prefer landscape images for hero
            if not layout_hints.get('is_portrait', False):
                score += 3
            
            # Prefer high resolution images
            width = dimensions.get('width', 0)
            if width > 3000:
                score += 2
            elif width > 2000:
                score += 1
            
            # Prefer images with high visual weight
            visual_weight = layout_hints.get('visual_weight', 'medium')
            if visual_weight == 'high':
                score += 2
            elif visual_weight == 'medium':
                score += 1
            
            # Penalize panoramic images for hero (they work better in grid)
            if layout_hints.get('is_panoramic', False):
                score -= 1
            
            scored_photos.append((score, photo))
        
        # Return the highest scoring photo
        scored_photos.sort(key=lambda x: x[0], reverse=True)
        return scored_photos[0][1] if scored_photos else photos[0]
    
    def arrange_grid_photos(self, photos: List[Dict], max_per_grid: int = 9) -> List[List[Dict]]:
        """Arrange photos into balanced grids considering aspect ratios and visual weight"""
        grids = []
        current_grid = []
        current_spans = 0
        max_spans_per_row = 3
        
        for photo in photos:
            metadata = photo.get('metadata', {})
            layout_hints = metadata.get('layout_hints', {})
            suggested_span = layout_hints.get('suggested_grid_span', 1)
            
            # Check if adding this photo would exceed grid capacity
            if (len(current_grid) >= max_per_grid or 
                (current_spans + suggested_span > max_spans_per_row and current_grid)):
                # Start new grid
                if current_grid:
                    grids.append(current_grid)
                current_grid = []
                current_spans = 0
            
            current_grid.append(photo)
            current_spans += suggested_span
            
            # Reset span counter if we filled a row
            if current_spans >= max_spans_per_row:
                current_spans = 0
        
        # Add final grid if it has photos
        if current_grid:
            grids.append(current_grid)
        
        return grids
    
    def generate_gallery_html(self, photos: List[Dict], title: str) -> str:
        """Generate HTML for a photo gallery with smart layout based on metadata"""
        gallery_sections = []
        
        if not photos:
            return ""
        
        # Select the best hero image using metadata
        hero_photo = self.select_hero_image(photos)
        remaining_photos = [p for p in photos if p != hero_photo]
        
        # Add hero image
        if hero_photo:
            gallery_sections.append(f"""<div class="gallery">
    <div class="gallery-item full">
        {self._generate_responsive_image_html_with_metadata(hero_photo, title, loading="eager")}
    </div>
</div>""")
        
        # Arrange remaining photos into smart grids
        if remaining_photos:
            grids = self.arrange_grid_photos(remaining_photos)
            
            for grid_photos in grids:
                grid_html = ['<div class="gallery grid-smart">']
                for photo in grid_photos:
                    grid_html.append(f"""    <div class="gallery-item">
        {self._generate_responsive_image_html_with_metadata(photo, title)}
    </div>""")
                grid_html.append('</div>')
                gallery_sections.append('\n'.join(grid_html))
        
        return '\n\n'.join(gallery_sections)
    
    def _generate_responsive_image_html_with_metadata(self, photo: Dict, alt_text: str, loading: str = "lazy", use_webp: bool = True) -> str:
        """Generate HTML for a responsive image using metadata"""
        urls = photo.get('urls', {})
        metadata = photo.get('metadata', {})
        dimensions = metadata.get('dimensions', {})
        layout_hints = metadata.get('layout_hints', {})
        
        width = dimensions.get('width', 800)
        height = dimensions.get('height', 600)
        
        # Add CSS classes based on metadata
        css_classes = []
        if layout_hints.get('is_portrait', False):
            css_classes.append('portrait')
        if layout_hints.get('is_panoramic', False):
            css_classes.append('panoramic')
        
        visual_weight = layout_hints.get('visual_weight', 'medium')
        css_classes.append(f'visual-{visual_weight}')
        
        suggested_span = layout_hints.get('suggested_grid_span', 1)
        css_classes.append(f'span-{suggested_span}')
        
        class_attr = f' class="{" ".join(css_classes)}"' if css_classes else ''
        
        if use_webp and isinstance(next(iter(urls.values()), {}), dict):
            # Handle WebP format URLs
            webp_srcset = []
            jpeg_srcset = []
            for size, format_urls in urls.items():
                if isinstance(format_urls, dict):
                    width_value = int(size.replace('w', ''))
                    if 'webp' in format_urls:
                        webp_srcset.append(f"{format_urls['webp']} {width_value}w")
                    if 'jpeg' in format_urls:
                        jpeg_srcset.append(f"{format_urls['jpeg']} {width_value}w")
            
            # Get fallback URL (prefer 1000w, then largest available)
            fallback_url = ""
            for size in ['1000w', '1500w', '2000w']:
                if size in urls and isinstance(urls[size], dict) and 'jpeg' in urls[size]:
                    fallback_url = urls[size]['jpeg']
                    break
            
            if not fallback_url and urls:
                # Use first available JPEG URL
                for format_urls in urls.values():
                    if isinstance(format_urls, dict) and 'jpeg' in format_urls:
                        fallback_url = format_urls['jpeg']
                        break
            
            return f"""<picture{class_attr}>
    <source type="image/webp" srcset="{', '.join(webp_srcset)}">
    <img src="{fallback_url}" 
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
                if isinstance(url, str):
                    width_value = int(size.replace('w', ''))
                    srcset.append(f"{url} {width_value}w")
            
            fallback_url = urls.get('1000w', '')
            if not fallback_url and urls:
                fallback_url = next(iter(urls.values()))
            
            return f"""<img src="{fallback_url}" 
         srcset="{', '.join(srcset)}"
         alt="{alt_text}" 
         width="{width}" 
         height="{height}"
         loading="{loading}"{class_attr}>"""