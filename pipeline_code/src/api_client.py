"""
Google Maps API client for fetching satellite imagery.
"""

import requests
import cv2
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class GoogleMapsClient:
    """Fetch satellite images from Google Maps Static API."""
    
    BASE_URL = "https://maps.googleapis.com/maps/api/staticmap"
    
    def __init__(self, api_key: str, zoom_level: int = 20,
                 image_size: int = 1024, map_scale: int = 2):
        self.api_key = api_key
        self.zoom_level = zoom_level
        self.image_size = image_size
        self.map_scale = map_scale
        self.request_size = f"{image_size // map_scale}x{image_size // map_scale}"
    
    def download_image(self, lat: float, lon: float, 
                       sample_id, output_folder: Path) -> str:
        """
        Download satellite image for given coordinates.
        
        Returns:
            Path to saved image file, or None if failed
        """
        params = {
            "center": f"{lat},{lon}",
            "zoom": self.zoom_level,
            "size": self.request_size,
            "scale": self.map_scale,
            "maptype": "satellite",
            "key": self.api_key
        }
        
        try:
            logger.info(f"Fetching image for sample {sample_id}")
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"API error {response.status_code} for sample {sample_id}")
                return None
            
            filename = output_folder / f"{sample_id}.jpg"
            filename.write_bytes(response.content)
            
            # Ensure correct size
            self._resize_if_needed(filename)
            
            return str(filename)
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout for sample {sample_id}")
            return None
        except Exception as e:
            logger.error(f"Download failed for {sample_id}: {e}")
            return None
    
    def _resize_if_needed(self, image_path: Path):
        """Resize image to target size if needed."""
        img = cv2.imread(str(image_path))
        if img is None:
            return
        
        h, w = img.shape[:2]
        if h != self.image_size or w != self.image_size:
            img = cv2.resize(img, (self.image_size, self.image_size))
            cv2.imwrite(str(image_path), img)
