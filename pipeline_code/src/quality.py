"""
Image Quality Control (QC) module.
Determines if an image is suitable for verification (VERIFIABLE vs NOT_VERIFIABLE).
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ImageQualityChecker:
    """Checks satellite imagery for quality issues (blur, darkness, clouds)."""
    
    def __init__(self, min_brightness=40, max_brightness=250, blur_threshold=100.0):
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.blur_threshold = blur_threshold

    def check_quality(self, image: np.ndarray) -> tuple[str, str]:
        """
        Analyze image quality.
        
        Returns:
            (status, reason)
            status: "VERIFIABLE" or "NOT_VERIFIABLE"
            reason: Description of the result or failure
        """
        if image is None or image.size == 0:
            return "NOT_VERIFIABLE", "Image load failed or empty"

        # 1. Blur Check (Laplacian Variance)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if laplacian_var < self.blur_threshold:
            return "NOT_VERIFIABLE", f"Image too blurry (score: {laplacian_var:.1f})"

        # 2. Brightness Check
        mean_brightness = np.mean(gray)
        if mean_brightness < self.min_brightness:
            return "NOT_VERIFIABLE", f"Image too dark (brightness: {mean_brightness:.1f})"
        if mean_brightness > self.max_brightness:
            # High brightness might be clouds or overexposure
            return "NOT_VERIFIABLE", f"Image too bright/cloudy (brightness: {mean_brightness:.1f})"

        # 3. Variance Check (Flat images/encoding errors)
        if np.std(gray) < 10:
             return "NOT_VERIFIABLE", "Image lacks detail/contrast"

        return "VERIFIABLE", "Quality OK"
