"""
Configuration module for solar panel detection system.
Supports both bbox and segmentation models with optional SAHI inference.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ==========================================================================
    # API Configuration
    # ==========================================================================
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    # ==========================================================================
    # Model Configuration
    # ==========================================================================
    # Model type: "bbox" for detection, "segmentation" for instance segmentation
    MODEL_TYPE = os.getenv('MODEL_TYPE', 'segmentation')
    
    # Model paths - auto-selected based on MODEL_TYPE
    MODEL_PATH_BBOX = os.getenv('MODEL_PATH_BBOX', './trained_model/best_bbox.pt')
    MODEL_PATH_SEG = os.getenv('MODEL_PATH_SEG', './trained_model/best_seg.pt')
    
    # Detection confidence threshold
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.15))
    
    # SAHI (Slicing Aided Hyper Inference) - helps with small/edge panels
    USE_SAHI = os.getenv('USE_SAHI', 'true').lower() == 'true'
    SAHI_SLICE_SIZE = int(os.getenv('SAHI_SLICE_SIZE', 512))
    SAHI_OVERLAP_RATIO = float(os.getenv('SAHI_OVERLAP_RATIO', 0.3))
    
    # ==========================================================================
    # Directory Paths
    # ==========================================================================
    INPUT_FOLDER = Path(os.getenv('INPUT_FOLDER', './input_folder'))
    OUTPUT_FOLDER = Path(os.getenv('OUTPUT_FOLDER', './prediction_files'))
    ARTEFACTS_FOLDER = Path(os.getenv('ARTEFACTS_FOLDER', './artefacts'))
    INPUT_FILENAME = "input_data.xlsx"
    
    # ==========================================================================
    # Image Settings (matches YOLOv12x training config)
    # ==========================================================================
    IMAGE_SIZE = 1024  # Model trained on 1024x1024
    MAP_REQUEST_SIZE = "512x512"
    MAP_SCALE = 2  # Results in 1024x1024 image
    ZOOM_LEVEL = int(os.getenv('ZOOM_LEVEL', 20))
    
    # ==========================================================================
    # Buffer Zones (in square feet)
    # ==========================================================================
    BUFFER_RADIUS_1_SQFT = 1200  # Primary search zone
    BUFFER_RADIUS_2_SQFT = 2400  # Extended search zone
    SQFT_TO_SQM = 0.092903
    
    # ==========================================================================
    # Detection Parameters
    # ==========================================================================
    MIN_OVERLAP_AREA = 10  # Minimum pixel overlap for valid detection
    MIN_PANEL_AREA_PX = 50  # Filter tiny false positives
    
    # ==========================================================================
    # Quality Control Thresholds
    # ==========================================================================
    BRIGHTNESS_THRESHOLD_LOW = 30
    BRIGHTNESS_THRESHOLD_HIGH = 225
    CLOUD_THRESHOLD = 0.7
    MIN_IMAGE_VARIANCE = 100
    
    @classmethod
    def get_model_path(cls):
        """Get model path based on MODEL_TYPE setting."""
        if cls.MODEL_TYPE == 'segmentation':
            path = Path(cls.MODEL_PATH_SEG)
        else:
            path = Path(cls.MODEL_PATH_BBOX)
        
        if not path.exists():
            # Try relative to script location
            alt_path = Path(__file__).parent.parent.parent / path.name
            if alt_path.exists():
                return str(alt_path)
            raise FileNotFoundError(f"Model not found: {path}")
        return str(path)
    
    @classmethod
    def is_segmentation_model(cls):
        """Check if using segmentation model."""
        return cls.MODEL_TYPE == 'segmentation'
    
    @classmethod
    def validate(cls):
        """Validate critical configuration values."""
        if not cls.GOOGLE_MAPS_API_KEY or cls.GOOGLE_MAPS_API_KEY == 'your_api_key_here':
            raise ValueError("Set GOOGLE_MAPS_API_KEY in .env file")
        
        # Validate model exists
        cls.get_model_path()
    
    @classmethod
    def setup_directories(cls):
        """Create necessary directories."""
        cls.INPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.ARTEFACTS_FOLDER.mkdir(parents=True, exist_ok=True)
