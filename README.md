# Solar Panel Detection System - Round 2

**EcoInnovators Ideathon 2026 | Team Akatsuki**

AI-powered rooftop PV detection system using YOLOv12x and satellite imagery.

---

## 📁 Repository Structure

```
├── pipeline_code/          # Inference code
│   ├── main.py             # Entry point
│   └── src/                # Core modules
├── environment_details/    # Dependencies
│   ├── requirements.txt
│   ├── environment.yml
│   └── python_version.txt
├── trained_model/          # Model weights
│   └── best_seg.pt         # Segmentation model
├── model_card/             # Model documentation
├── prediction_files/       # Output JSON files
├── artefacts/              # Output images & overlays
├── training_logs/          # Training metrics
└── README.md
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Using pip
pip install -r environment_details/requirements.txt

# Or using conda
conda env create -f environment_details/environment.yml
conda activate solar-detection
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your Google Maps API key
```

### 3. Prepare Input

Place your input file at `input_folder/input_data.xlsx` with columns:
- `sample_id` - Unique identifier
- `latitude` - WGS84 latitude
- `longitude` - WGS84 longitude

### 4. Run Pipeline

```bash
cd pipeline_code
python main.py
```

---

## ⚙️ Configuration

Set these in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_MAPS_API_KEY` | - | Required. Your API key |
| `MODEL_TYPE` | `segmentation` | `bbox` or `segmentation` |
| `USE_SAHI` | `true` | Enable sliced inference |
| `CONFIDENCE_THRESHOLD` | `0.15` | Detection threshold |
| `ZOOM_LEVEL` | `20` | Satellite image zoom |

---

## 📤 Output Format

### JSON Output (`prediction_files/`)

```json
{
  "sample_id": 1234,
  "lat": 12.9716,
  "lon": 77.5946,
  "has_solar": true,
  "confidence": 0.92,
  "buffer_radius_sqft": 1200,
  "pv_area_sqm_est": 23.5,
  "euclidean_distance_m_est": 2.3,
  "qc_status": "VERIFIABLE",
  "bbox_or_mask": "[[x1,y1], [x2,y2], ...]",
  "image_metadata": {...}
}
```

### Image Overlays (`artefacts/`)

- **Green filled**: Selected target panel
- **Red filled**: Other detected panels  
- **Yellow circle**: Buffer zone

---

## 🔧 Model Details

- **Architecture**: YOLOv12x (segmentation)
- **Training Size**: 1024×1024
- **Task**: Solar panel instance segmentation
- **Inference**: Optional SAHI for improved detection

See `model_card/model_card.pdf` for full documentation.

---

## 📊 Round 2 Improvements

1. **Fixed Type 1-2**: Improved detection with lower threshold + SAHI
2. **Fixed Type 5**: Centroid-based buffer zone validation
3. **Fixed Type 7**: Better panel selection scoring
4. **Fixed Type 8**: Filled overlays (not just borders)

---

## 👥 Team Akatsuki

EcoInnovators Ideathon 2026
