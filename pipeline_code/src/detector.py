"""
Solar panel detection with YOLOv12x.
Supports both bbox and segmentation models with optional SAHI inference.
"""

import logging
import numpy as np
from pathlib import Path
from shapely.geometry import Polygon

logger = logging.getLogger(__name__)


class SolarPanelDetector:
    """YOLOv12x-based solar panel detector with optional SAHI."""
    
    def __init__(self, model_path: str, model_type: str = 'segmentation',
                 confidence: float = 0.15, use_sahi: bool = True,
                 slice_size: int = 512, overlap_ratio: float = 0.3):
        self.model_path = model_path
        self.model_type = model_type
        self.confidence = confidence
        self.use_sahi = use_sahi
        self.slice_size = slice_size
        self.overlap_ratio = overlap_ratio
        self.model = None
    
    def initialize(self):
        """Load detection model."""
        device = self._get_device()
        
        if self.use_sahi:
            from sahi import AutoDetectionModel
            logger.info(f"Loading model with SAHI: {self.model_path}")
            self.model = AutoDetectionModel.from_pretrained(
                model_type='yolov8',  # SAHI uses yolov8 for YOLOv11/v12
                model_path=self.model_path,
                confidence_threshold=self.confidence,
                device=device
            )
        else:
            from ultralytics import YOLO
            logger.info(f"Loading YOLO model directly: {self.model_path}")
            self.model = YOLO(self.model_path)
        
        logger.info(f"Model loaded on {device} (type: {self.model_type}, sahi: {self.use_sahi})")
    
    def detect(self, image_path: str) -> list:
        """
        Detect solar panels in image.
        
        Returns:
            List of (polygon, confidence, is_segmentation) tuples
        """
        if self.model is None:
            raise RuntimeError("Call initialize() first")
        
        logger.info(f"Detecting panels in: {Path(image_path).name}")
        
        if self.use_sahi:
            return self._detect_with_sahi(image_path)
        else:
            return self._detect_direct(image_path)
    
    def _detect_with_sahi(self, image_path: str) -> list:
        """Run detection with SAHI slicing."""
        from sahi.predict import get_sliced_prediction
        
        result = get_sliced_prediction(
            str(image_path),
            self.model,
            slice_height=self.slice_size,
            slice_width=self.slice_size,
            overlap_height_ratio=self.overlap_ratio,
            overlap_width_ratio=self.overlap_ratio
        )
        
        polygons = []
        for pred in result.object_prediction_list:
            if pred.score.value < self.confidence:
                continue
            
            poly, is_seg = self._extract_polygon(pred)
            if poly and poly.area > 50:  # Filter tiny detections
                polygons.append((poly, pred.score.value, is_seg))
        
        self._log_detection_stats(polygons)
        return polygons
    
    def _detect_direct(self, image_path: str) -> list:
        """Run direct YOLO inference without slicing."""
        results = self.model(image_path, conf=self.confidence, verbose=False)[0]
        
        polygons = []
        
        # Check for segmentation masks
        if results.masks is not None and len(results.masks) > 0:
            for i, mask in enumerate(results.masks.xy):
                if len(mask) >= 3:
                    poly = Polygon(mask)
                    if poly.is_valid and poly.area > 50:
                        conf = float(results.boxes.conf[i])
                        polygons.append((poly, conf, True))
        
        # Fall back to bounding boxes
        if not polygons and results.boxes is not None:
            for box in results.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                poly = Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)])
                conf = float(box.conf)
                polygons.append((poly, conf, False))
        
        self._log_detection_stats(polygons)
        return polygons
    
    def _extract_polygon(self, prediction) -> tuple:
        """Extract polygon from SAHI prediction. Returns (polygon, is_segmentation)."""
        # Try segmentation mask first
        if hasattr(prediction, 'mask') and prediction.mask is not None:
            try:
                segmentation = prediction.mask.to_coco_segmentation()
                if segmentation:
                    best_seg = max(segmentation, key=len) if len(segmentation) > 1 else segmentation[0]
                    coords = [(best_seg[i], best_seg[i+1]) for i in range(0, len(best_seg), 2)]
                    if len(coords) >= 3:
                        poly = Polygon(coords)
                        if poly.is_valid:
                            return poly, True
                        poly = poly.buffer(0)  # Fix invalid geometry
                        if poly.is_valid:
                            return poly, True
            except Exception as e:
                logger.debug(f"Mask extraction failed: {e}")
        
        # Fall back to bounding box
        bbox = prediction.bbox
        x1, y1, x2, y2 = bbox.minx, bbox.miny, bbox.maxx, bbox.maxy
        return Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)]), False
    
    def _log_detection_stats(self, polygons: list):
        """Log detection statistics."""
        seg_count = sum(1 for _, _, is_seg in polygons if is_seg)
        bbox_count = len(polygons) - seg_count
        logger.info(f"Detected {len(polygons)} panels ({seg_count} segmented, {bbox_count} bbox)")
    
    @staticmethod
    def _get_device() -> str:
        """Determine best available device."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda:0"
        except ImportError:
            pass
        return "cpu"
