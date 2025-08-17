from typing import List, Dict, Optional
from .base import LayoutStrategy


class JustifiedLayoutStrategy(LayoutStrategy):
    """Justified layout strategy that creates gapless rows based on aspect ratios"""
    
    @property
    def name(self) -> str:
        return "justified"
    
    @property
    def description(self) -> str:
        return "Justified rows layout that respects aspect ratios and creates gapless rows"
    
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
            
            # Penalize panoramic images for hero (they work better in justified rows)
            if layout_hints.get('is_panoramic', False):
                score -= 1
            
            scored_photos.append((score, photo))
        
        # Return the highest scoring photo
        scored_photos.sort(key=lambda x: x[0], reverse=True)
        return scored_photos[0][1] if scored_photos else photos[0]
    
    def arrange_grid_photos(self, photos: List[Dict], max_per_grid: int = 9) -> List[List[Dict]]:
        """This method is kept for compatibility but not used in justified layout"""
        # For justified layout, we use _arrange_justified_rows instead
        return [photos]
    
    def _arrange_justified_rows(self, photos: List[Dict], target_ratio: float = 4.5) -> List[List[Dict]]:
        """Arrange photos into justified rows based on aspect ratios"""
        rows = []
        current_row = []
        current_ratio_sum = 0.0
        
        for photo in photos:
            metadata = photo.get('metadata', {})
            dimensions = metadata.get('dimensions', {})
            layout_hints = metadata.get('layout_hints', {})
            
            # Calculate aspect ratio
            width = dimensions.get('width', 1)
            height = dimensions.get('height', 1)
            aspect_ratio = width / height
            
            # Handle panoramic images - give them their own row
            if layout_hints.get('is_panoramic', False) or aspect_ratio > 2.5:
                # Finish current row if it has images
                if current_row:
                    rows.append(current_row)
                    current_row = []
                    current_ratio_sum = 0.0
                
                # Add panoramic image as single-image row
                rows.append([photo])
                continue
            
            # Check if adding this image would exceed target ratio
            if current_ratio_sum + aspect_ratio > target_ratio and current_row:
                # Finish current row
                rows.append(current_row)
                current_row = []
                current_ratio_sum = 0.0
            
            # Add image to current row
            current_row.append(photo)
            current_ratio_sum += aspect_ratio
        
        # Add final row if it has images
        if current_row:
            # Handle underfilled last row
            if len(current_row) == 1 and len(rows) > 0 and len(rows[-1]) > 1:
                # Move one image from previous row to balance
                moved_photo = rows[-1].pop()
                current_row.insert(0, moved_photo)
            rows.append(current_row)
        
        return rows
    
    def generate_gallery_html(self, photos: List[Dict], title: str) -> str:
        """Generate HTML for a photo gallery with justified layout"""
        gallery_sections = []
        
        if not photos:
            return ""
        
        # Select the best hero image
        hero_photo = self.select_hero_image(photos)
        remaining_photos = [p for p in photos if p != hero_photo]
        
        # Add hero image
        if hero_photo:
            gallery_sections.append(f"""<div class="gallery">
    <div class="gallery-item full">
        {self._generate_responsive_image_html_with_metadata(hero_photo, title, loading="eager")}
    </div>
</div>""")
        
        # Use justified layout for remaining photos
        if remaining_photos:
            justified_html = self._generate_justified_layout_html(remaining_photos, title)
            gallery_sections.append(justified_html)
        
        return '\n\n'.join(gallery_sections)
    
    def _generate_justified_layout_html(self, photos: List[Dict], title: str) -> str:
        """Generate HTML for justified rows layout"""
        rows = self._arrange_justified_rows(photos)
        
        gallery_html = ['<div class="gallery layout-strat-justified">']
        
        for row in rows:
            gallery_html.append('    <div class="jg-row">')
            
            for photo in row:
                # Calculate aspect ratio for flex-grow
                metadata = photo.get('metadata', {})
                dimensions = metadata.get('dimensions', {})
                width = dimensions.get('width', 1)
                height = dimensions.get('height', 1)
                aspect_ratio = width / height
                
                # Generate image HTML with flex style
                image_html = self._generate_responsive_image_html_with_metadata(photo, title)
                gallery_html.append(f'        <div class="gallery-item jg-item" style="flex: {aspect_ratio:.3f} 1 0%;">')
                gallery_html.append(f'            {image_html}')
                gallery_html.append('        </div>')
            
            gallery_html.append('    </div>')
        
        gallery_html.append('</div>')
        return '\n'.join(gallery_html)
    
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
         loading="{loading}"
         style="object-fit: cover; width: 100%; height: 100%;">
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
         loading="{loading}"
         style="object-fit: cover; width: 100%; height: 100%;"{class_attr}>"""