"""
Solar Panel Detection API Server
FastAPI backend with endpoints for analysis.
"""

import sys
from pathlib import Path

# Add project root to sys.path to allow importing from pipeline_code
# Assuming backend/server.py is running, we go up one level to project root
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.append(str(project_root))

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from pipeline_code.src.config import AppConfig
from pipeline_code.src.detector import SolarDetector
from pipeline_code.src.api_client import GoogleMapsClient

# Initialize global components
detector: Optional[SolarDetector] = None
maps_client: Optional[GoogleMapsClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize detector and components on startup."""
    global detector, maps_client
    
    detector = SolarDetector(AppConfig.MODEL_PATH)
    
    maps_client = GoogleMapsClient(
        api_key=AppConfig.GOOGLE_MAPS_API_KEY,
        zoom_level=AppConfig.ZOOM_LEVEL,
        image_size=AppConfig.IMAGE_SIZE,
        map_scale=AppConfig.MAP_SCALE
    )
    
    yield
    print("Shutting down...")

app = FastAPI(
    title="Solar Panel Detection API",
    description="AI-powered rooftop solar panel detection - EcoInnovators 2026",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    lat: float
    lon: float
    sample_id: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    model_type: str
    model_path: str


@app.get("/api/health")
async def health_check():
    """Check API status."""
    model_type = "Unknown"
    if detector and hasattr(detector, 'task'):
        model_type = detector.task.upper()
        
    return {
        "status": "online",
        "app": "Solar Panel Detection API",
        "model_loaded": detector is not None,
        "model_type": model_type,
        "config": {
            "image_size": AppConfig.IMAGE_SIZE,
            "confidence": AppConfig.CONFIDENCE
        }
    }

@app.post("/api/analyze")
async def analyze_location(request: AnalyzeRequest):
    """Analyze a location for solar panels."""
    global detector, maps_client
    
    if detector is None or maps_client is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    

    output_dir = Path("artefacts")
    
    sample_id = request.sample_id or f"{request.lat:.4f}_{request.lon:.4f}"
    sample_output_dir = output_dir / sample_id
    sample_output_dir.mkdir(parents=True, exist_ok=True)

    # Fetch image using shared client
    image_path = maps_client.download_image(
        request.lat, request.lon, sample_id, sample_output_dir
    )
    
    if not image_path:
        raise HTTPException(status_code=500, detail="Failed to fetch satellite image")
    
    # Run detection
    result = detector.detect(image_path, request.lat, request.lon)
    
    return result

@app.get("/files/{sample_id}/{filename}")
async def get_file(sample_id: str, filename: str):
    """Serve generated images."""
    file_path = Path("artefacts") / sample_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
