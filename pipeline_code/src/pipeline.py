"""
Main detection pipeline for solar panel detection.
Processes input coordinates and generates predictions with artifacts.
"""

import json
import logging
import pandas as pd
from pathlib import Path
from tqdm import tqdm

from .config import AppConfig as Config
from .api_client import GoogleMapsClient
from .detector import SolarDetector

logger = logging.getLogger(__name__)


class SolarDetectionPipeline:
    """Complete pipeline for solar panel detection from satellite imagery."""
    
    def __init__(self):
        # Initialize components
        self.maps_client = GoogleMapsClient(
            api_key=Config.GOOGLE_MAPS_API_KEY,
            zoom_level=Config.ZOOM_LEVEL,
            image_size=Config.IMAGE_SIZE,
            map_scale=Config.MAP_SCALE
        )
        
        self.detector = SolarDetector(
            model_path=Config.MODEL_PATH
        )
        
    def run(self, input_file: str = None, output_folder: str = None):
        """Execute the complete detection pipeline."""
        self._print_banner()
        
        # Use config defaults if not provided
        input_path = Path(input_file) if input_file else Path(Config.INPUT_FOLDER) / "input_data.xlsx"
        artefacts_dir = Path(output_folder) if output_folder else Path(Config.ARTEFACTS_FOLDER)
        predictions_dir = Path(Config.OUTPUT_FOLDER)
        
        # Ensure directories exist
        artefacts_dir.mkdir(parents=True, exist_ok=True)
        predictions_dir.mkdir(parents=True, exist_ok=True)
        
        if not input_path.exists():
             logger.info(f"Input file {input_path} not found. Creating sample.")
             self._create_sample_input(input_path)
        
        df = self._load_input(input_path)
        if df is None:
            return
        
        # Process all samples
        results = []
        total = len(df)
        
        with tqdm(total=total, desc="Processing") as pbar:
            for idx, row in df.iterrows():
                result = self._process_sample(row, artefacts_dir)
                if result:
                    results.append(result)
                pbar.update(1)
        
        # Save combined results to predictions folder
        self._save_results(results, predictions_dir)
        self._print_summary(results)
    
    def _process_sample(self, row, base_dir: Path) -> dict:
        """Process a single location sample."""
        sample_id = str(row['sample_id'])
        lat = float(row['latitude'])
        lon = float(row['longitude'])
        
        # Create sample specific folder
        sample_dir = base_dir / sample_id
        sample_dir.mkdir(parents=True, exist_ok=True)
        
        # Download satellite image
        image_path = self.maps_client.download_image(
            lat, lon, sample_id, sample_dir
        )
        
        if not image_path:
            logger.warning(f"Skipped {sample_id} - download failed")
            return None
        
        # Run detection (Includes visualization generation)
        result = self.detector.detect(image_path, lat, lon)
        
        # Save individual JSON result for consistency
        json_path = sample_dir / f"{sample_id}.json"
        
        # Clean up result for file saving (remove internal keys if needed, or just save all)
        # The result from detector.detect is already compliant with the requested format
        
        json_path.write_text(json.dumps(result, indent=2))
        
        return result
    
    def _create_sample_input(self, path: Path):
        """Create a sample input file if none exists."""
        df = pd.DataFrame({
            'sample_id': [1001, 1002],
            'latitude': [23.908454, 28.7041],
            'longitude': [71.182617, 77.1025]
        })
        df.to_excel(path, index=False)

    def _load_input(self, input_path: Path) -> pd.DataFrame:
        """Load input Excel file."""
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
    
    def _save_results(self, results: list, output_dir: Path):
        """Save combined results JSON."""
        output_path = output_dir / "all_predictions.json"
        output_path.write_text(json.dumps(results, indent=2))
        logger.info(f"Saved combined results: {output_path}")
    
    def _print_banner(self):
        """Print startup banner."""
        print("=" * 60)
        print("  Solar Panel Detection Pipeline - Refactored")
        print(f"  Image Size: {Config.IMAGE_SIZE}x{Config.IMAGE_SIZE}")
        print("=" * 60)
    
    def _print_summary(self, results: list):
        """Print execution summary."""
        total = len(results)
        solar_found = sum(1 for r in results if r['has_solar'])
        
        print("\n" + "=" * 60)
        print("  PIPELINE COMPLETE")
        print(f"  Total: {total} | Solar Found: {solar_found}")
        print("=" * 60)
