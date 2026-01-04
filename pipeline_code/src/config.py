"""
Configuration settings for the Solar Panel Detection Backend.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Get project root (parent of pipeline_code)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class AppConfig:
    """Application configuration."""
    
    @staticmethod
    def _resolve_path(path_str: str) -> str:
        """Resolve path relative to project root if not absolute."""
        if not path_str:
            return ""
        path = Path(path_str)
        if path.is_absolute():
            return str(path)
        # Assume entries in .env are relative to PROJECT_ROOT
        return str((PROJECT_ROOT / path_str).resolve())

    # Model Settings
    # Env var should path to the model file (.pt)
    MODEL_PATH = _resolve_path(os.getenv('MODEL_PATH', 'trained_model/OBB-1024-FT-ON-640px-MODEL.pt'))
    CONFIDENCE = 0.25
    FALLBACK_CONFIDENCE = 0.25
    
    # Map & Image Settings
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
    IMAGE_SIZE = 1024
    ZOOM_LEVEL = 20
    MAP_SCALE = 2
    
    # Analysis Settings
    BUFFER_1200 = 1200
    BUFFER_2400 = 2400
    PADDING = 50
    
    # Folder Settings
    INPUT_FOLDER = _resolve_path(os.getenv('INPUT_FOLDER', 'input_folder'))
    OUTPUT_FOLDER = _resolve_path(os.getenv('OUTPUT_FOLDER', 'prediction_files'))
    ARTEFACTS_FOLDER = _resolve_path(os.getenv('ARTEFACTS_FOLDER', 'artefacts'))
