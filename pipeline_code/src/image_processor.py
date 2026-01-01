"""
Image quality assessment for satellite imagery.
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ImageQualityChecker:
    """Check if image quality is sufficient for reliable detection."""
    
    def __init__(self, brightness_low: int = 30, brightness_high: int = 225,
                 cloud_threshold: float = 0.7, min_variance: float = 100):
        self.brightness_low = brightness_low
        self.brightness_high = brightness_high
        self.cloud_threshold = cloud_threshold
        self.min_variance = min_variance
    
    def check_quality(self, image_path: str) -> tuple:
        """
        Assess image quality for detection.
        
        Returns:
            (is_verifiable: bool, reason: str)
        """
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                return False, "Failed to load image"
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Check brightness (shadows/poor lighting)
            mean_brightness = np.mean(gray)
            if mean_brightness < self.brightness_low:
                return False, "Image too dark"
            
            # Check cloud cover (too bright)
            bright_ratio = np.sum(gray > self.brightness_high) / gray.size
            if bright_ratio > self.cloud_threshold:
                return False, "Heavy cloud cover"
            
            # Check image detail (variance)
            variance = np.var(gray)
            if variance < self.min_variance:
                return False, "Low image detail"
            
            return True, "Good quality"
            
        except Exception as e:
            logger.error(f"Quality check error: {e}")
            return False, f"Error: {str(e)}"
