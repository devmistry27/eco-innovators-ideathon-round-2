# EcoInnovators Team Akatsuki - Solar Panel Detection System

## Overview
This system utilizes a hybrid YOLOv8-OBB model to detect rooftop solar panels in satellite imagery. It supports both standard Bounding Box (BBox) and Oriented Bounding Box (OBB) detection, providing precise localization, area estimation, and verification metrics.

## Key Features
- **Fetch:** Automatic retrieval of high-resolution satellite imagery via Google Maps Static API.
- **Classify:** Binary classification (Present/Not Present) with adaptive buffer zones (1200 sq.ft / 2400 sq.ft).
- **Quantify:** Estimation of solar panel area (m²) matching the panel tilt.
- **Verify:** Calculation of Euclidean distance from the target coordinate.
- **Explainability:** Generation of visual artifacts with overlays and QC status.

## Repository Structure
```
my-app/
├── pipeline_code/          # Source code for the detection pipeline
├── environment_details/    # Dependencies and environment config
├── trained_model/          # YOLOv8 OBB trained model weights (.pt)
├── model_card/             # Model documentation (LaTeX/PDF)
├── prediction_files/       # output JSON predictions
├── artefacts/             # Generated image overlays and artifacts
├── training_logs/          # Training metrics and logs
└── README.md              # This file
```

## Installation

1. **Prerequisites:**
   - Python 3.10+
   - CUDA-enabled GPU (recommended for faster inference)

2. **Setup Environment:**
   ```bash
   pip install -r environment_details/requirements.txt
   ```
   *Alternatively, use Conda:*
   ```bash
   conda env create -f environment_details/environment.yml
   conda activate solar-detection
   ```

3. **Configuration:**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_MAPS_API_KEY=your_api_key_here
   MODEL_PATH=trained_model/OBB-1024-FT-ON-640px-MODEL.pt
   ```

## Usage

### Running the Pipeline
To run the full detection pipeline on an input Excel file:

```bash
python pipeline_code/main.py --input input.xlsx --output prediction_files
```

- **Input:** Excel file containing `sample_id`, `latitude`, `longitude`.
- **Output:** JSON results in `prediction_files/` and image artifacts in `artefacts/`.

### API Backend (Optional)
To start the FastAPI server for real-time inference:

```bash
python backend/server.py
```
Access the API at `http://localhost:8008`.

## Model Details
- **Architecture:** YOLOv8-Medium OBB
- **Input Resolution:** 1024px (Fine-tuned)
- **Performance:** mAP@50: 0.867 | Precision: 0.855 | Recall: 0.815

## Authors
**Team Akatsuki** - EcoInnovators 2026
