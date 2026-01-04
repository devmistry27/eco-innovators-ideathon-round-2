"""
Visualization module for solar panel detection.
Handles drawing of OBB polygons and overlays.
"""

import cv2
import numpy as np


class Visualizer:
    """Handles image annotation and overlay creation."""
    
    @staticmethod
    def create_overlay(
        image: np.ndarray,
        result: dict,
        center: tuple,
        radius: float,
        output_path: str
    ) -> None:
        """Create and save visualization overlay."""
        overlay = image.copy()
        h, w = overlay.shape[:2]
        
        # 1. Darken outside buffer area
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(mask, (int(center[0]), int(center[1])), int(radius), 255, -1)
        overlay[mask == 0] = (overlay[mask == 0] * 0.4).astype(np.uint8)
        
        # 2. Draw buffer circle
        cv2.circle(overlay, (int(center[0]), int(center[1])), int(radius), (0, 255, 255), 2)
        
        # 3. Draw detections
        selected_idx = result.get('selected_idx', -1)
        all_boxes = result.get('all_boxes', [])
        all_confs = result.get('all_confs', [])
        
        for i, box_data in enumerate(all_boxes):
            is_selected = (i == selected_idx)
            color = (0, 255, 0) if is_selected else (0, 0, 255)
            
            obb_points = box_data.get('obb_points')
            if obb_points:
                Visualizer._draw_obb(overlay, obb_points, color, is_selected)
                cx = np.mean([p[0] for p in obb_points])
                cy = np.mean([p[1] for p in obb_points])
            else:
                bbox = box_data.get('bbox', [])
                if len(bbox) == 4:
                    Visualizer._draw_bbox(overlay, bbox, color, is_selected)
                    cx = (bbox[0] + bbox[2]) / 2
                    cy = (bbox[1] + bbox[3]) / 2
                else:
                    continue
            
            if is_selected and i < len(all_confs):
                conf = all_confs[i]
                cv2.putText(
                    overlay,
                    f"{conf:.2f}",
                    (int(cx) - 15, int(cy) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )

        # 4. Draw markers and text
        cv2.drawMarker(
            overlay,
            (int(center[0]), int(center[1])),
            (0, 0, 255),
            cv2.MARKER_CROSS,
            20,
            2
        )
        
        buffer_sqft = result.get('buffer_sqft', 0)
        cv2.putText(
            overlay,
            f"Buffer: {buffer_sqft} sqft",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        
        cv2.imwrite(output_path, overlay)

    @staticmethod
    def _draw_obb(img: np.ndarray, points: list, color: tuple, fill: bool = False) -> None:
        """Draw Oriented Bounding Box."""
        pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
        
        cv2.polylines(img, [pts], True, color, 2)
        
        if fill:
            overlay_copy = img.copy()
            cv2.fillPoly(overlay_copy, [pts], color)
            cv2.addWeighted(overlay_copy, 0.2, img, 0.8, 0, img)

    @staticmethod
    def _draw_bbox(img: np.ndarray, bbox: list, color: tuple, fill: bool = False) -> None:
        """Draw Standard Axis-Aligned Bounding Box (fallback)."""
        x1, y1, x2, y2 = [int(v) for v in bbox]
        
        if fill:
            overlay_copy = img.copy()
            cv2.rectangle(overlay_copy, (x1, y1), (x2, y2), color, -1)
            cv2.addWeighted(overlay_copy, 0.2, img, 0.8, 0, img)
            
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
