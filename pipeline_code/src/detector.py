"""
Core inference logic for Solar Panel Detection.
"""

import cv2
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO

from .config import AppConfig
from .visualizer import Visualizer
from .quality import ImageQualityChecker
from .utils import (
    calculate_meters_per_pixel,
    calculate_radius_from_area_sqft,
    calculate_intersection_area,
    calculate_box_area_pixels,
    calculate_distance,
    get_box_center,
    obb_to_bbox,
    enhance_saturation,
    calculate_polygon_area
)


class SolarDetector:
    """Handles loading the model and running multi-stage inference."""
    
    def __init__(self, model_path: str):
        self.model = YOLO(model_path) # Auto-detect task type
        self.quality_checker = ImageQualityChecker()
        # Determine model type for logging/logic if needed (optional)
        self.task = self.model.task if hasattr(self.model, 'task') else 'detect'

    def detect(self, image_path: str, lat: float, lon: float) -> dict:
        """Main entry point for detection on an image."""
        img = cv2.imread(image_path)
        if img is None:
            return self._create_error_result("Image load failed", lat, lon)

        qc_status, qc_reason = self.quality_checker.check_quality(img)

        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        
        mpp = calculate_meters_per_pixel(lat, AppConfig.ZOOM_LEVEL, AppConfig.MAP_SCALE)
        radius_1200 = calculate_radius_from_area_sqft(AppConfig.BUFFER_1200, mpp)
        radius_2400 = calculate_radius_from_area_sqft(AppConfig.BUFFER_2400, mpp)
        
        result = self._execute_pipeline(img, center, radius_1200, radius_2400, mpp)
        result['qc_status'] = qc_status
        result['qc_reason'] = qc_reason
        
        overlay_path = Path(image_path).parent / f"{Path(image_path).stem}_overlay.png"
        
        Visualizer.create_overlay(
            image=img,
            result=result,
            center=center,
            radius=result['radius'],
            output_path=str(overlay_path)
        )
        
        return self._format_response(result, lat, lon, image_path, str(overlay_path))

    def _execute_pipeline(self, img: np.ndarray, center: tuple, 
                         r1200: float, r2400: float, mpp: float) -> dict:
        """Runs the multi-stage detection strategy."""
        result = {
            'has_solar': False,
            'confidence': 0.0,
            'bbox': [],
            'obb_points': [],
            'buffer_sqft': AppConfig.BUFFER_2400,
            'radius': r2400,
            'area_sqm': 0.0,
            'distance_m': 0.0,
            'method': 'none',
            'all_boxes': [],
            'all_confs': [],
            'selected_idx': -1
        }
        
        boxes, confs = self._predict(img, AppConfig.CONFIDENCE)
        result['all_boxes'] = boxes
        result['all_confs'] = confs
        
        best_idx, _ = self._find_best_match(boxes, center, r1200)
        if best_idx != -1:
            return self._finalize_result(result, boxes, confs, best_idx, AppConfig.BUFFER_1200, r1200, mpp, center, 'initial_1200')

        img_sat = enhance_saturation(img, 1.5)
        sat_boxes, sat_confs = self._predict(img_sat, AppConfig.FALLBACK_CONFIDENCE)
        
        best_idx, _ = self._find_best_match(sat_boxes, center, r1200)
        if best_idx != -1:
            result['all_boxes'] = sat_boxes
            result['all_confs'] = sat_confs
            return self._finalize_result(result, sat_boxes, sat_confs, best_idx, AppConfig.BUFFER_1200, r1200, mpp, center, 'saturated_1200')

        best_idx, _ = self._find_best_match(boxes, center, r2400)
        if best_idx != -1:
            result['all_boxes'] = boxes
            result['all_confs'] = confs
            return self._finalize_result(result, boxes, confs, best_idx, AppConfig.BUFFER_2400, r2400, mpp, center, 'initial_2400')

        best_idx, _ = self._find_best_match(sat_boxes, center, r2400)
        if best_idx != -1:
            result['all_boxes'] = sat_boxes
            result['all_confs'] = sat_confs
            return self._finalize_result(result, sat_boxes, sat_confs, best_idx, AppConfig.BUFFER_2400, r2400, mpp, center, 'saturated_2400')

        # No panel found within any buffer zone
        # Return has_solar=False with all detections for visualization
        all_pool_boxes = boxes if boxes else sat_boxes
        all_pool_confs = confs if confs else sat_confs
        result['all_boxes'] = all_pool_boxes
        result['all_confs'] = all_pool_confs
        
        return result

    def _predict(self, img: np.ndarray, conf: float) -> tuple:
        """Run YOLO inference (OBB or BBox)."""
        results = self.model(img, conf=conf, verbose=False, max_det=300)
        res = results[0]
        
        boxes = []
        confs = []
        
        # Check for OBB first
        if res.obb is not None and len(res.obb) > 0:
            obb_boxes = res.obb.xyxyxyxy.cpu().numpy()
            obb_confs = res.obb.conf.cpu().numpy()
            
            for i in range(len(obb_boxes)):
                points = [[float(p[0]), float(p[1])] for p in obb_boxes[i].reshape(-1, 2)]
                bbox = obb_to_bbox(points)
                boxes.append({
                    'bbox': bbox,
                    'obb_points': points
                })
                confs.append(float(obb_confs[i]))
                
        # Fallback to standard BBox
        elif res.boxes is not None and len(res.boxes) > 0:
            det_boxes = res.boxes.xyxy.cpu().numpy()
            det_confs = res.boxes.conf.cpu().numpy()
            
            for i in range(len(det_boxes)):
                x1, y1, x2, y2 = det_boxes[i]
                bbox = [float(x1), float(y1), float(x2), float(y2)]
                # Create 4 points for compatibility with OBB visualizer
                points = [[float(x1), float(y1)], [float(x2), float(y1)], [float(x2), float(y2)], [float(x1), float(y2)]]
                boxes.append({
                    'bbox': bbox,
                    'obb_points': points
                })
                confs.append(float(det_confs[i]))
                
        return boxes, confs

    def _find_best_match(self, boxes: list, center: tuple, radius: float) -> tuple:
        """Find the box that overlaps most with the center buffer."""
        best_idx = -1
        max_overlap = 0.0
        
        for i, data in enumerate(boxes):
            overlap = calculate_intersection_area(data['bbox'], center, radius)
            if overlap > max_overlap:
                max_overlap = overlap
                best_idx = i
                
        return best_idx, max_overlap

    def _finalize_result(self, result: dict, boxes: list, confs: list, idx: int,
                        buf_sqft: int, radius: float, mpp: float, 
                        center: tuple, method: str) -> dict:
        """Populate the result dictionary with the winning detection."""
        winner = boxes[idx]
        bbox = winner['bbox']
        obb = winner.get('obb_points')
        
        box_center = get_box_center(bbox)
        
        if obb:
            area_px = calculate_polygon_area(obb)
        else:
            area_px = calculate_box_area_pixels(bbox)
            
        result.update({
            'has_solar': True,
            'confidence': confs[idx],
            'bbox': bbox,
            'obb_points': obb if obb else [],
            'buffer_sqft': buf_sqft,
            'radius': radius,
            'area_sqm': area_px * (mpp ** 2),
            'distance_m': calculate_distance(box_center, center) * mpp,
            'method': method,
            'all_boxes': boxes,
            'all_confs': confs,
            'selected_idx': idx
        })
        return result

    def _format_response(self, result: dict, lat: float, lon: float, 
                        img_path: str, overlay_path: str) -> dict:
        """Format final JSON API response."""
        sid = Path(img_path).stem
        
        if result.get('obb_points'):
            bbox_str = json.dumps(result['obb_points'])
        elif result.get('bbox'):
            bbox_str = json.dumps(result['bbox'])
        else:
            bbox_str = "[]"

        return {
            "sample_id": sid,
            "lat": lat,
            "lon": lon,
            "has_solar": result['has_solar'],
            "confidence": round(result['confidence'], 4),
            "pv_area_sqm_est": round(result['area_sqm'], 2),
            "buffer_radius_sqft": result['buffer_sqft'],
            "euclidean_distance_m_est": round(result['distance_m'], 2),
            "qc_status": result.get('qc_status', "VERIFIABLE"),
            "bbox_or_mask": bbox_str,
            "detection_method": result['method'],
            "image_url": f"/files/{sid}/{sid}.jpg",
            "overlay_url": f"/files/{sid}/{Path(overlay_path).name}",
            "image_metadata": {
                "source": "Google Maps Static API",
                "capture_date": datetime.now().strftime("%Y-%m-%d"),
                "qc_reason": result.get('qc_reason', "OK")
            }
        }

    def _create_error_result(self, msg: str, lat: float, lon: float) -> dict:
        """Return a safe error dictionary."""
        return {
            "sample_id": f"{lat:.4f}_{lon:.4f}",
            "lat": lat,
            "lon": lon,
            "has_solar": False,
            "confidence": 0.0,
            "error": msg,
            "bbox_or_mask": "[]"
        }
