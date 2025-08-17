from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any


class LayoutStrategy(ABC):
    """Base class for gallery layout strategies"""
    
    @abstractmethod
    def select_hero_image(self, photos: List[Dict]) -> Optional[Dict]:
        """Select the best image for the hero/first position"""
        pass
    
    @abstractmethod
    def arrange_grid_photos(self, photos: List[Dict], max_per_grid: int = 9) -> List[List[Dict]]:
        """Arrange photos into grids"""
        pass
    
    @abstractmethod
    def generate_gallery_html(self, photos: List[Dict], title: str) -> str:
        """Generate HTML for the complete gallery"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name for CLI selection"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Strategy description"""
        pass