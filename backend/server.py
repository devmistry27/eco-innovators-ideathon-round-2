"""
Solar Panel Detection API Server
Simple FastAPI wrapper around existing pipeline.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add pipeline_code to path
PIPELINE_PATH = Path(__file__).parent.parent / "pipeline_code"
sys.path.insert(0, str(PIPELINE_PATH))

from src.config import Config
from src.detector import SolarPanelDetector
from src.api_client import GoogleMapsClient
from src.image_processor import ImageQualityChecker
from src.geometry import (
    get_meters_per_pixel, buffer_radius_to_pixels,
    find_best_panel, calculate_euclidean_distance, encode_polygon
)
from src.visualizer import DetectionVisualizer


# Global detector instance (loaded once)
detector: Optional[SolarPanelDetector] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize detector on startup."""
    global detector
    print("Loading detection model...")
    detector = SolarPanelDetector(
        model_path=Config.get_model_path(),
        model_type=Config.MODEL_TYPE,
        confidence=Config.CONFIDENCE_THRESHOLD,
        use_sahi=Config.USE_SAHI,
        slice_size=Config.SAHI_SLICE_SIZE,
        overlap_ratio=Config.SAHI_OVERLAP_RATIO
    )
    detector.initialize()
    print("Model loaded successfully!")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Solar Panel Detection API",
    description="AI-powered rooftop solar panel detection",
    version="2.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class AnalyzeRequest(BaseModel):
    lat: float
    lon: float
    sample_id: Optional[str] = None


class AnalyzeResponse(BaseModel):
    sample_id: str
    lat: float
    lon: float
    has_solar: bool
    confidence: float
    pv_area_sqm_est: float
    buffer_radius_sqft: int
    euclidean_distance_m_est: float
    qc_status: str
    image_url: str
    overlay_url: str


class HealthResponse(BaseModel):
    status: str
    model_type: str
    use_sahi: bool


# Initialize components
maps_client = GoogleMapsClient(
    api_key=Config.GOOGLE_MAPS_API_KEY,
    zoom_level=Config.ZOOM_LEVEL,
    image_size=Config.IMAGE_SIZE,
    map_scale=Config.MAP_SCALE
)

quality_checker = ImageQualityChecker(
    brightness_low=Config.BRIGHTNESS_THRESHOLD_LOW,
    brightness_high=Config.BRIGHTNESS_THRESHOLD_HIGH,
    cloud_threshold=Config.CLOUD_THRESHOLD,
    min_variance=Config.MIN_IMAGE_VARIANCE
)

visualizer = DetectionVisualizer()


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check API status."""
    return HealthResponse(
        status="online",
        model_type=Config.MODEL_TYPE,
        use_sahi=Config.USE_SAHI
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_location(request: AnalyzeRequest):
    """Analyze a single location for solar panels."""
    global detector
    
    if detector is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Generate sample ID if not provided
    sample_id = request.sample_id or f"{request.lat:.4f}_{request.lon:.4f}"
    
    # Create output directory
    output_dir = Path("artefacts") / sample_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Download satellite image
    image_path = maps_client.download_image(
        request.lat, request.lon, sample_id, output_dir
    )
    
    if not image_path:
        raise HTTPException(status_code=500, detail="Failed to fetch satellite image")
    
    # Check image quality
    is_verifiable, quality_reason = quality_checker.check_quality(image_path)
    
    # Run detection
    all_polygons = detector.detect(image_path)
    
    # Calculate geometry
    center_px = (Config.IMAGE_SIZE // 2, Config.IMAGE_SIZE // 2)
    meters_per_px = get_meters_per_pixel(request.lat, Config.ZOOM_LEVEL, Config.MAP_SCALE)
    
    radius_1_px = buffer_radius_to_pixels(
        Config.BUFFER_RADIUS_1_SQFT, Config.SQFT_TO_SQM,
        request.lat, Config.ZOOM_LEVEL, Config.MAP_SCALE
    )
    radius_2_px = buffer_radius_to_pixels(
        Config.BUFFER_RADIUS_2_SQFT, Config.SQFT_TO_SQM,
        request.lat, Config.ZOOM_LEVEL, Config.MAP_SCALE
    )
    
    # Find best panel
    result = _find_best_detection(all_polygons, center_px, radius_1_px, radius_2_px, meters_per_px)
    
    # Calculate distance
    euclidean_dist = calculate_euclidean_distance(
        result['polygon'], center_px, meters_per_px
    )
    
    # Generate overlay
    overlay_path = output_dir / f"{sample_id}_overlay.png"
    visualizer.draw_results(
        image_path, all_polygons, result['polygon'],
        center_px, result['radius_px'], result['buffer_sqft'],
        str(overlay_path)
    )
    
    return AnalyzeResponse(
        sample_id=sample_id,
        lat=request.lat,
        lon=request.lon,
        has_solar=result['has_solar'],
        confidence=round(result['confidence'], 4),
        pv_area_sqm_est=round(result['area_sqm'], 2),
        buffer_radius_sqft=result['buffer_sqft'],
        euclidean_distance_m_est=round(euclidean_dist, 2),
        qc_status="VERIFIABLE" if is_verifiable else "NOT_VERIFIABLE",
        image_url=f"/files/{sample_id}/{sample_id}.jpg",
        overlay_url=f"/files/{sample_id}/{sample_id}_overlay.png"
    )


def _find_best_detection(polygons, center_px, radius_1_px, radius_2_px, meters_per_px):
    """Find best panel in buffer zones."""
    result = {
        'has_solar': False,
        'buffer_sqft': Config.BUFFER_RADIUS_2_SQFT,
        'area_sqm': 0.0,
        'confidence': 0.0,
        'polygon': None,
        'radius_px': radius_2_px
    }
    
    if not polygons:
        return result
    
    # Try 1200 sq.ft buffer first
    poly, conf, overlap = find_best_panel(polygons, center_px, radius_1_px, Config.MIN_OVERLAP_AREA)
    
    if poly is not None:
        result.update({
            'has_solar': True,
            'buffer_sqft': Config.BUFFER_RADIUS_1_SQFT,
            'area_sqm': poly.area * (meters_per_px ** 2),
            'confidence': conf,
            'polygon': poly,
            'radius_px': radius_1_px
        })
        return result
    
    # Try 2400 sq.ft buffer
    poly, conf, overlap = find_best_panel(polygons, center_px, radius_2_px, Config.MIN_OVERLAP_AREA)
    
    if poly is not None:
        result.update({
            'has_solar': True,
            'buffer_sqft': Config.BUFFER_RADIUS_2_SQFT,
            'area_sqm': poly.area * (meters_per_px ** 2),
            'confidence': conf,
            'polygon': poly,
            'radius_px': radius_2_px
        })
    
    return result


# Serve artefact files
@app.get("/files/{sample_id}/{filename}")
async def get_file(sample_id: str, filename: str):
    """Serve generated images."""
    file_path = Path("artefacts") / sample_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
