"""
Geometric calculations for buffer zones and panel selection.
Improved logic to fix Type 1, 2, 5, 7 detection issues.
"""

import math
import json
import logging
from shapely.geometry import Point, Polygon

logger = logging.getLogger(__name__)


def get_meters_per_pixel(lat: float, zoom: int, scale: int = 2) -> float:
    """
    Calculate ground resolution at given latitude and zoom level.
    
    Formula: resolution = 156543.03392 * cos(lat) / 2^zoom / scale
    """
    return 156543.03392 * math.cos(math.radians(lat)) / (2 ** zoom) / scale


def buffer_radius_to_pixels(buffer_sqft: float, sqft_to_sqm: float, 
                            lat: float, zoom: int, scale: int) -> float:
    """
    Convert buffer area (sq.ft) to buffer radius (pixels).
    
    Steps:
    1. Convert sq.ft to sq.m
    2. Calculate radius from circular area
    3. Convert meters to pixels at location
    """
    area_sqm = buffer_sqft * sqft_to_sqm
    radius_m = math.sqrt(area_sqm / math.pi)
    meters_per_px = get_meters_per_pixel(lat, zoom, scale)
    return radius_m / meters_per_px


def find_best_panel(polygons: list, center_px: tuple, buffer_radius_px: float,
                    min_overlap: float = 10) -> tuple:
    """
    Find the best panel within buffer zone using improved scoring.
    
    Fixes for competition issues:
    - Type 1/2: Better overlap calculation, prioritize larger panels
    - Type 5: Use centroid distance check, not just mask overlap
    - Type 7: Return panels sorted by score, not just first match
    
    Scoring: overlap_area * (1 + size_bonus) * confidence
    - Larger panels get higher size_bonus
    - Ensures we pick the main panel, not a small distant one
    
    Returns:
        (best_polygon, confidence, overlap_area) or (None, 0, 0)
    """
    if not polygons:
        return None, 0.0, 0.0
    
    buffer_circle = Point(center_px).buffer(buffer_radius_px)
    
    candidates = []
    for item in polygons:
        poly = item[0]
        conf = item[1]
        
        try:
            # Check if polygon intersects buffer zone
            if not buffer_circle.intersects(poly):
                continue
            
            # Calculate overlap area
            intersection = buffer_circle.intersection(poly)
            overlap_area = intersection.area
            
            if overlap_area < min_overlap:
                continue
            
            # Calculate centroid distance (for Type 5 fix)
            centroid = poly.centroid
            centroid_dist = Point(center_px).distance(centroid)
            
            # Reject if centroid is too far (1.5x buffer radius)
            if centroid_dist > buffer_radius_px * 1.5:
                logger.debug(f"Rejected panel: centroid too far ({centroid_dist:.0f}px)")
                continue
            
            # Calculate panel area for size bonus
            panel_area = poly.area
            
            # Score: prioritize overlap, then size, then confidence
            # Size bonus: larger panels get up to 50% boost
            size_bonus = min(panel_area / 10000, 0.5)
            score = overlap_area * (1 + size_bonus) * conf
            
            candidates.append({
                'polygon': poly,
                'confidence': conf,
                'overlap': overlap_area,
                'score': score,
                'area': panel_area
            })
            
        except Exception as e:
            logger.warning(f"Error processing polygon: {e}")
            continue
    
    if not candidates:
        logger.info("No panels within buffer zone")
        return None, 0.0, 0.0
    
    # Sort by score (highest first)
    candidates.sort(key=lambda x: x['score'], reverse=True)
    best = candidates[0]
    
    logger.info(f"Selected panel: area={best['area']:.0f}px², "
                f"overlap={best['overlap']:.0f}px², conf={best['confidence']:.2f}")
    
    return best['polygon'], best['confidence'], best['overlap']


def calculate_euclidean_distance(polygon: Polygon, center_px: tuple, 
                                  meters_per_px: float) -> float:
    """Calculate distance from panel centroid to center point in meters."""
    if polygon is None:
        return 0.0
    
    centroid = polygon.centroid
    dx = centroid.x - center_px[0]
    dy = centroid.y - center_px[1]
    distance_px = math.sqrt(dx**2 + dy**2)
    return distance_px * meters_per_px


def encode_polygon(poly: Polygon) -> str:
    """Encode polygon coordinates to JSON string."""
    if poly is None:
        return ""
    coords = list(poly.exterior.coords)
    return json.dumps([[round(x, 2), round(y, 2)] for x, y in coords])
