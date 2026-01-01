"""
Main detection pipeline for solar panel detection.
Processes input coordinates and generates predictions with artifacts.
"""

import json
import logging
import pandas as pd
from pathlib import Path

from .config import Config
from .api_client import GoogleMapsClient
from .image_processor import ImageQualityChecker
from .detector import SolarPanelDetector
from .geometry import (
    get_meters_per_pixel, buffer_radius_to_pixels, 
    find_best_panel, calculate_euclidean_distance, encode_polygon
)
from .visualizer import DetectionVisualizer

logger = logging.getLogger(__name__)


class SolarDetectionPipeline:
    """Complete pipeline for solar panel detection from satellite imagery."""
    
    def __init__(self):
        self.config = Config
        
        # Initialize components
        self.maps_client = GoogleMapsClient(
            api_key=Config.GOOGLE_MAPS_API_KEY,
            zoom_level=Config.ZOOM_LEVEL,
            image_size=Config.IMAGE_SIZE,
            map_scale=Config.MAP_SCALE
        )
        
        self.quality_checker = ImageQualityChecker(
            brightness_low=Config.BRIGHTNESS_THRESHOLD_LOW,
            brightness_high=Config.BRIGHTNESS_THRESHOLD_HIGH,
            cloud_threshold=Config.CLOUD_THRESHOLD,
            min_variance=Config.MIN_IMAGE_VARIANCE
        )
        
        self.detector = SolarPanelDetector(
            model_path=Config.get_model_path(),
            model_type=Config.MODEL_TYPE,
            confidence=Config.CONFIDENCE_THRESHOLD,
            use_sahi=Config.USE_SAHI,
            slice_size=Config.SAHI_SLICE_SIZE,
            overlap_ratio=Config.SAHI_OVERLAP_RATIO
        )
        
        self.visualizer = DetectionVisualizer()
    
    def run(self):
        """Execute the complete detection pipeline."""
        self._print_banner()
        
        # Validate and setup
        Config.validate()
        Config.setup_directories()
        
        # Load input data
        input_path = Config.INPUT_FOLDER / Config.INPUT_FILENAME
        df = self._load_input(input_path)
        if df is None:
            return
        
        # Initialize model
        self.detector.initialize()
        
        # Process all samples
        results = []
        total = len(df)
        
        for idx, row in df.iterrows():
            result = self._process_sample(row, idx + 1, total)
            if result:
                results.append(result)
        
        # Save combined results
        self._save_results(results)
        self._print_summary(results)
    
    def _process_sample(self, row, current: int, total: int) -> dict:
        """Process a single location sample."""
        sample_id = row['sample_id']
        lat = float(row['latitude'])
        lon = float(row['longitude'])
        
        logger.info(f"[{current}/{total}] Processing sample {sample_id}")
        
        # Create output folders
        prediction_folder = Config.OUTPUT_FOLDER / str(sample_id)
        artefact_folder = Config.ARTEFACTS_FOLDER / str(sample_id)
        prediction_folder.mkdir(parents=True, exist_ok=True)
        artefact_folder.mkdir(parents=True, exist_ok=True)
        
        # Download satellite image
        image_path = self.maps_client.download_image(
            lat, lon, sample_id, artefact_folder
        )
        if not image_path:
            logger.warning(f"Skipped {sample_id} - download failed")
            return None
        
        # Check image quality
        is_verifiable, quality_reason = self.quality_checker.check_quality(image_path)
        
        # Run detection
        all_polygons = self.detector.detect(image_path)
        
        # Calculate geometry
        center_px = (Config.IMAGE_SIZE // 2, Config.IMAGE_SIZE // 2)
        meters_per_px = get_meters_per_pixel(lat, Config.ZOOM_LEVEL, Config.MAP_SCALE)
        
        radius_1_px = buffer_radius_to_pixels(
            Config.BUFFER_RADIUS_1_SQFT, Config.SQFT_TO_SQM,
            lat, Config.ZOOM_LEVEL, Config.MAP_SCALE
        )
        radius_2_px = buffer_radius_to_pixels(
            Config.BUFFER_RADIUS_2_SQFT, Config.SQFT_TO_SQM,
            lat, Config.ZOOM_LEVEL, Config.MAP_SCALE
        )
        
        # Find best panel in buffer zones
        result = self._find_best_detection(
            all_polygons, center_px, radius_1_px, radius_2_px, meters_per_px
        )
        
        # Calculate euclidean distance
        euclidean_dist = calculate_euclidean_distance(
            result['polygon'], center_px, meters_per_px
        )
        
        # Build output record
        output = {
            "sample_id": int(sample_id),
            "lat": lat,
            "lon": lon,
            "has_solar": result['has_solar'],
            "confidence": round(result['confidence'], 4),
            "pv_area_sqm_est": round(result['area_sqm'], 2),
            "buffer_radius_sqft": result['buffer_sqft'],
            "euclidean_distance_m_est": round(euclidean_dist, 2),
            "qc_status": "VERIFIABLE" if is_verifiable else "NOT_VERIFIABLE",
            "bbox_or_mask": encode_polygon(result['polygon']),
            "image_metadata": {
                "source": "Google Maps Static API",
                "size": f"{Config.IMAGE_SIZE}x{Config.IMAGE_SIZE}",
                "meters_per_px": round(meters_per_px, 5),
                "quality_check": quality_reason
            }
        }
        
        # Save individual JSON
        json_path = prediction_folder / f"{sample_id}.json"
        json_path.write_text(json.dumps(output, indent=2))
        
        # Generate overlay visualization
        overlay_path = artefact_folder / f"{sample_id}_overlay.png"
        self.visualizer.draw_results(
            image_path, all_polygons, result['polygon'],
            center_px, result['radius_px'], result['buffer_sqft'],
            str(overlay_path)
        )
        
        return output
    
    def _find_best_detection(self, polygons: list, center_px: tuple,
                             radius_1_px: float, radius_2_px: float,
                             meters_per_px: float) -> dict:
        """Find best panel in buffer zones (1200 sq.ft first, then 2400 sq.ft)."""
        result = {
            'has_solar': False,
            'buffer_sqft': Config.BUFFER_RADIUS_2_SQFT,
            'area_sqm': 0.0,
            'confidence': 0.0,
            'polygon': None,
            'radius_px': radius_2_px
        }
        
        if not polygons:
            logger.info("No panels detected in image")
            return result
        
        # Try smaller buffer first (1200 sq.ft)
        poly, conf, overlap = find_best_panel(
            polygons, center_px, radius_1_px, Config.MIN_OVERLAP_AREA
        )
        
        if poly is not None:
            result.update({
                'has_solar': True,
                'buffer_sqft': Config.BUFFER_RADIUS_1_SQFT,
                'area_sqm': poly.area * (meters_per_px ** 2),
                'confidence': conf,
                'polygon': poly,
                'radius_px': radius_1_px
            })
            logger.info(f"Solar found in 1200 sq.ft buffer")
            return result
        
        # Try larger buffer (2400 sq.ft)
        poly, conf, overlap = find_best_panel(
            polygons, center_px, radius_2_px, Config.MIN_OVERLAP_AREA
        )
        
        if poly is not None:
            result.update({
                'has_solar': True,
                'buffer_sqft': Config.BUFFER_RADIUS_2_SQFT,
                'area_sqm': poly.area * (meters_per_px ** 2),
                'confidence': conf,
                'polygon': poly,
                'radius_px': radius_2_px
            })
            logger.info(f"Solar found in 2400 sq.ft buffer")
        else:
            logger.info("Panels detected but outside buffer zones")
        
        return result
    
    def _load_input(self, input_path: Path) -> pd.DataFrame:
        """Load input Excel file."""
        if not input_path.exists():
            logger.info(f"Creating sample input: {input_path}")
            df = pd.DataFrame({
                'sample_id': [1001, 1002],
                'latitude': [23.908454, 28.7041],
                'longitude': [71.182617, 77.1025]
            })
            df.to_excel(input_path, index=False)
        
        try:
            df = pd.read_excel(input_path)
            required = ['sample_id', 'latitude', 'longitude']
            
            if not all(col in df.columns for col in required):
                logger.error(f"Missing required columns: {required}")
                return None
            
            logger.info(f"Loaded {len(df)} samples")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load input: {e}")
            return None
    
    def _save_results(self, results: list):
        """Save combined results JSON."""
        output_path = Config.OUTPUT_FOLDER / "all_predictions.json"
        output_path.write_text(json.dumps(results, indent=2))
        logger.info(f"Saved combined results: {output_path}")
    
    def _print_banner(self):
        """Print startup banner."""
        print("=" * 60)
        print("  Solar Panel Detection Pipeline - Round 2")
        print(f"  Model: {Config.MODEL_TYPE} | SAHI: {Config.USE_SAHI}")
        print(f"  Image Size: {Config.IMAGE_SIZE}x{Config.IMAGE_SIZE}")
        print("=" * 60)
    
    def _print_summary(self, results: list):
        """Print execution summary."""
        total = len(results)
        solar_found = sum(1 for r in results if r['has_solar'])
        verifiable = sum(1 for r in results if r['qc_status'] == 'VERIFIABLE')
        
        print("\n" + "=" * 60)
        print("  PIPELINE COMPLETE")
        print(f"  Total: {total} | Solar: {solar_found} | Verifiable: {verifiable}")
        print("=" * 60)
