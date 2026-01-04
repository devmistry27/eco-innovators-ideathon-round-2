"""
Utility functions for solar panel detection pipeline.
Geometry calculations and image processing helpers.
"""

import math
import cv2
import numpy as np
from shapely.geometry import Point, Polygon, box


# =============================================================================
# GEOMETRY CALCULATIONS
# =============================================================================

def calculate_meters_per_pixel(lat: float, zoom: int = 20, scale: int = 2) -> float:
    """
    Calculate meters per pixel at a given latitude and zoom level.
    """
    lat_rad = math.radians(lat)
    mpp = (156543.03392 * math.cos(lat_rad)) / (2 ** zoom)
    return mpp / scale


def calculate_radius_from_area_sqft(area_sqft: float, meters_per_pixel: float) -> float:
    """
    Convert area in square feet to radius in pixels.
    """
    area_sqm = area_sqft * 0.092903
    radius_m = math.sqrt(area_sqm / math.pi)
    radius_px = radius_m / meters_per_pixel
    return radius_px


def calculate_intersection_area(bbox: list, center: tuple, radius: float) -> float:
    """
    Calculate the intersection area between a bounding box and a circular buffer.
    """
    if not bbox or len(bbox) < 4:
        return 0.0
    
    x1, y1, x2, y2 = bbox[:4]
    box_poly = box(x1, y1, x2, y2)
    
    # Create circle approximation (32 points)
    circle = Point(center).buffer(radius, resolution=32)
    
    try:
        intersection = box_poly.intersection(circle)
        return intersection.area
    except Exception:
        return 0.0


def calculate_box_area_pixels(bbox: list) -> float:
    """Calculate area of a bounding box in pixels²."""
    if not bbox or len(bbox) < 4:
        return 0.0
    x1, y1, x2, y2 = bbox[:4]
    return abs((x2 - x1) * (y2 - y1))


def calculate_polygon_area(points: list) -> float:
    """Calculate area of a polygon from list of points."""
    if not points or len(points) < 3:
        return 0.0
    try:
        poly = Polygon(points)
        return poly.area if poly.is_valid else 0.0
    except Exception:
        return 0.0


def calculate_distance(point1: tuple, point2: tuple) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


def get_box_center(bbox: list) -> tuple:
    """Get center point of a bounding box."""
    if not bbox or len(bbox) < 4:
        return (0, 0)
    x1, y1, x2, y2 = bbox[:4]
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def obb_to_bbox(obb_points: np.ndarray) -> list:
    """Convert OBB (4 corner points) to axis-aligned bounding box."""
    if len(obb_points) < 4:
        return []
    x_coords = [p[0] for p in obb_points]
    y_coords = [p[1] for p in obb_points]
    return [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]


# =============================================================================
# IMAGE PROCESSING
# =============================================================================

def enhance_saturation(image: np.ndarray, factor: float = 1.5) -> np.ndarray:
    """
    Enhance image saturation to make solar panels more visible.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255).astype(np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def crop_buffer_region(image: np.ndarray, center: tuple, radius: float, 
                       padding: int = 30) -> tuple:
    """
    Crop image to focus on buffer region for better detection of small panels.
    Returns: (cropped_image, offset, scale_factor)
    """
    h, w = image.shape[:2]
    
    x1 = max(0, int(center[0] - radius - padding))
    y1 = max(0, int(center[1] - radius - padding))
    x2 = min(w, int(center[0] + radius + padding))
    y2 = min(h, int(center[1] + radius + padding))
    
    cropped = image[y1:y2, x1:x2]
    offset = (x1, y1)
    
    return cropped, offset, 1.0


def adjust_boxes_for_crop(boxes: list, offset: tuple) -> list:
    """Adjust bounding box coordinates after cropping."""
    adjusted = []
    for bbox in boxes:
        # Check if bbox is dict (our new internal format) or list
        # The calling code passes list of new format dicts, but wait...
        # In detector.py: `c_boxes, c_confs = self._predict(...)` returns list of dicts.
        # Then `c_boxes = adjust_boxes_for_crop(c_boxes, offset)` is called.
        # So `boxes` here is list of dicts.
        
        if isinstance(bbox, dict):
            # Handle dict format
            b = bbox['bbox']
            if len(b) >= 4:
                x1, y1, x2, y2 = b[:4]
                new_b = [
                    x1 + offset[0],
                    y1 + offset[1],
                    x2 + offset[0],
                    y2 + offset[1]
                ]
                # We need to return the full dict structure adjusted
                new_bbox = bbox.copy()
                new_bbox['bbox'] = new_b
                
                # Also adjust obb_points if present
                if bbox.get('obb_points'):
                     new_pts = []
                     for p in bbox['obb_points']:
                         new_pts.append([p[0] + offset[0], p[1] + offset[1]])
                     new_bbox['obb_points'] = new_pts
                
                adjusted.append(new_bbox)
        else:
            # Fallback for raw lists (legacy support if needed, though we shouldn't need it)
            if len(bbox) >= 4:
                x1, y1, x2, y2 = bbox[:4]
                adjusted.append([
                    x1 + offset[0],
                    y1 + offset[1],
                    x2 + offset[0],
                    y2 + offset[1]
                ])
                
    return adjusted
