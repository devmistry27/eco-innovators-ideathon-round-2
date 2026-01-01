"""
Visualization module for detection results.
Fixed: Non-selected panels are now FILLED with red (not thin borders).
"""

import cv2
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DetectionVisualizer:
    """Create overlay images showing detection results."""
    
    # Colors (BGR format)
    COLOR_GREEN = (0, 255, 0)      # Selected panel
    COLOR_RED = (0, 0, 255)        # Other panels
    COLOR_YELLOW = (0, 255, 255)   # Buffer zone
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_MAGENTA = (255, 0, 255)  # Centroid marker
    
    def __init__(self, alpha: float = 0.4):
        """Initialize with overlay transparency."""
        self.alpha = alpha
    
    def draw_results(self, image_path: str, all_polygons: list, 
                     best_polygon, center_px: tuple, buffer_radius_px: float,
                     buffer_sqft: int, output_path: str):
        """
        Create visualization overlay.
        
        Args:
            image_path: Original satellite image
            all_polygons: All detected panels [(polygon, confidence, is_seg), ...]
            best_polygon: The selected panel (or None)
            center_px: Image center point
            buffer_radius_px: Buffer zone radius in pixels
            buffer_sqft: Buffer area in sq.ft (for annotation)
            output_path: Where to save the overlay
        """
        img = cv2.imread(str(image_path))
        if img is None:
            logger.error(f"Cannot load image: {image_path}")
            return
        
        # Create overlay layer for blending
        overlay = img.copy()
        
        # 1. Draw buffer zone circle (yellow)
        self._draw_buffer_zone(overlay, center_px, buffer_radius_px)
        
        # 2. Draw all OTHER panels in FILLED RED
        for panel_data in all_polygons:
            poly = panel_data[0]
            if best_polygon is not None and poly.equals(best_polygon):
                continue  # Skip selected panel
            self._draw_panel_filled(overlay, poly, self.COLOR_RED)
        
        # 3. Draw selected panel in FILLED GREEN
        if best_polygon is not None:
            self._draw_panel_filled(overlay, best_polygon, self.COLOR_GREEN)
            self._draw_centroid_marker(overlay, best_polygon)
        
        # 4. Blend overlay with original
        result = cv2.addWeighted(overlay, self.alpha, img, 1 - self.alpha, 0)
        
        # 5. Redraw contours on top for crisp edges
        for panel_data in all_polygons:
            poly = panel_data[0]
            if best_polygon is not None and poly.equals(best_polygon):
                self._draw_contour(result, poly, self.COLOR_GREEN, 3)
            else:
                self._draw_contour(result, poly, self.COLOR_RED, 2)
        
        # 6. Add annotations
        has_solar = best_polygon is not None
        self._add_annotations(result, buffer_sqft, has_solar)
        self._add_legend(result)
        
        # Save result
        cv2.imwrite(str(output_path), result)
        logger.info(f"Saved overlay: {Path(output_path).name}")
    
    def _draw_buffer_zone(self, img, center: tuple, radius: float):
        """Draw yellow buffer zone circle with center dot."""
        if radius > 0:
            cx, cy = int(center[0]), int(center[1])
            cv2.circle(img, (cx, cy), int(radius), self.COLOR_YELLOW, 3)
            cv2.circle(img, (cx, cy), 5, self.COLOR_YELLOW, -1)
    
    def _draw_panel_filled(self, img, polygon, color: tuple):
        """Draw filled polygon panel."""
        coords = np.array(polygon.exterior.coords, dtype=np.int32)
        cv2.fillPoly(img, [coords], color)
    
    def _draw_contour(self, img, polygon, color: tuple, thickness: int):
        """Draw polygon contour."""
        coords = np.array(polygon.exterior.coords, dtype=np.int32)
        cv2.polylines(img, [coords], True, color, thickness)
    
    def _draw_centroid_marker(self, img, polygon):
        """Draw centroid marker with TARGET PANEL label."""
        centroid = polygon.centroid
        cx, cy = int(centroid.x), int(centroid.y)
        
        # Magenta dot with white outline
        cv2.circle(img, (cx, cy), 8, self.COLOR_MAGENTA, -1)
        cv2.circle(img, (cx, cy), 8, self.COLOR_WHITE, 2)
        
        # Label with background
        label = "TARGET PANEL"
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale, thickness = 0.6, 2
        
        (tw, th), _ = cv2.getTextSize(label, font, scale, thickness)
        lx, ly = cx - tw // 2, cy - 20
        
        cv2.rectangle(img, (lx - 5, ly - th - 5), (lx + tw + 5, ly + 5), 
                     self.COLOR_BLACK, -1)
        cv2.putText(img, label, (lx, ly), font, scale, self.COLOR_WHITE, thickness)
    
    def _add_annotations(self, img, buffer_sqft: int, has_solar: bool):
        """Add status text in top-left corner."""
        h, w = img.shape[:2]
        
        # Semi-transparent background
        bg = np.zeros((80, 320, 3), dtype=np.uint8)
        roi = img[0:80, 0:320]
        if roi.shape == bg.shape:
            img[0:80, 0:320] = cv2.addWeighted(roi, 0.3, bg, 0.7, 0)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Buffer info
        cv2.putText(img, f"Buffer: {buffer_sqft} sq.ft", 
                   (10, 30), font, 0.7, self.COLOR_WHITE, 2)
        
        # Detection status
        if has_solar:
            cv2.putText(img, "SOLAR CONFIRMED", (10, 60), 
                       font, 0.7, self.COLOR_GREEN, 2)
        else:
            cv2.putText(img, "NO SOLAR FOUND", (10, 60), 
                       font, 0.7, self.COLOR_RED, 2)
    
    def _add_legend(self, img):
        """Add legend in bottom-left corner."""
        h, w = img.shape[:2]
        
        # Semi-transparent background
        legend_h, legend_w = 90, 180
        y_start = h - legend_h
        
        bg = np.zeros((legend_h, legend_w, 3), dtype=np.uint8)
        roi = img[y_start:h, 0:legend_w]
        if roi.shape == bg.shape:
            img[y_start:h, 0:legend_w] = cv2.addWeighted(roi, 0.3, bg, 0.7, 0)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        y = y_start + 20
        
        cv2.putText(img, "Legend:", (10, y), font, 0.5, self.COLOR_WHITE, 1)
        
        # Buffer zone
        y += 20
        cv2.circle(img, (18, y - 4), 6, self.COLOR_YELLOW, -1)
        cv2.putText(img, "Buffer Zone", (30, y), font, 0.45, self.COLOR_WHITE, 1)
        
        # Selected panel
        y += 20
        cv2.rectangle(img, (12, y - 10), (24, y + 2), self.COLOR_GREEN, -1)
        cv2.putText(img, "Selected Panel", (30, y), font, 0.45, self.COLOR_WHITE, 1)
        
        # Other panels
        y += 20
        cv2.rectangle(img, (12, y - 10), (24, y + 2), self.COLOR_RED, -1)
        cv2.putText(img, "Other Panels", (30, y), font, 0.45, self.COLOR_WHITE, 1)
