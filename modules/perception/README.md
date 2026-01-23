# Module A: Perception Layer

> **Hardware**: VIOFO A119 V3 Dashcam (2560x1440@30fps, Novatek chipset)  
> **GPS Source**: Binary metadata (exiftool) - 1Hz GPS interpolated to 30fps  
> **Model**: YOLOv8n with MPS acceleration (M4 MacBook Pro)

YOLOv8-based traffic sign detection and ROI extraction for dashcam videos.

## Overview

Processes dashcam videos with YOLOv8 detection and GPS metadata extraction:

- **Input**: VIOFO A119 V3 MP4 videos with embedded GPS (Novatek chipset)
- **Detection**: YOLOv8n identifies traffic lights and stop signs
- **GPS Extraction**: Binary metadata via exiftool (1Hz → interpolated to 30fps)
- **Output**: CSV detections + 256×256 ROI patches
- **Performance**: ~100 FPS inference with M4 MPS acceleration

---

## Features

- **MPS Acceleration**: M4 Metal Performance Shaders (~100 FPS inference)
- **Binary GPS Extraction**: exiftool reads Novatek metadata (1Hz → 30fps interpolation)
- **Smart Sampling**: 1 FPS default (processes ~3% of frames)
- **ROI Extraction**: 256×256 patches for bandwidth optimization
- **Target Classes**: Traffic lights and stop signs

---

## Quick Start

### Install Dependencies
```bash
cd modules/perception

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Download YOLOv8 weights (auto-downloads on first run)
python detect_and_extract.py --help
```

### Process Single Video
```bash
python detect_and_extract.py \
  --video ../../data/videos/dashcam_001.mp4 \
  --output-csv ../../data/detections/detections.csv \
  --output-patches ../../data/roi_patches \
  --sample-fps 1 \
  --conf 0.25 \
  --device mps
```

### Example Output
```
🚀 Loading YOLOv8 model on mps...
📹 Processing video: ../../data/videos/dashcam_001.mp4
🎬 Video FPS: 30, Total Frames: 9000
⏱️  Sampling: 1 frame every 30 frames (1 FPS)
⏳ Processed 100 frames, 237 detections (98.5 FPS)
⏳ Processed 200 frames, 468 detections (99.2 FPS)

============================================================
✅ Processing Complete!
============================================================
📊 Total Frames: 9000
🔍 Processed Frames: 300
🎯 Total Detections: 473
⏱️  Elapsed Time: 3.12s
🚀 Average FPS: 96.15
⚡ Average Inference: 10.41ms
📁 CSV Output: ../../data/detections/detections.csv
🖼️  ROI Patches: ../../data/roi_patches
============================================================
```

---

## Output Format

### CSV Schema (Input for Module B)
```csv
frame_number,timestamp_sec,u,v,confidence,class_name,vehicle_lat,vehicle_lon,heading
75,2.500,1737.28,630.06,0.5249,stop sign,43.7900,-79.3140,45.0
185,6.167,2141.59,200.01,0.3381,traffic light,43.7905,-79.3138,47.5
```

**Columns**:
- `frame_number`: Video frame index
- `timestamp_sec`: Video timestamp (seconds)
- `u`, `v`: Pixel coordinates (bottom-center of bounding box)
- `confidence`: YOLO confidence score (0-1)
- `class_name`: "stop sign" or "traffic light"
- `vehicle_lat`, `vehicle_lon`: GPS from frame overlay
- `heading`: Vehicle heading in degrees (0°=North)

### ROI Patches
- **Format**: JPEG (256×256 pixels)
- **Naming**: `frame_{frame_number:06d}_det_{detection_id:04d}.jpg`
- **Location**: `../../data/roi_patches/`
- **Purpose**: Bandwidth optimization for cloud upload

---

## Configuration

### CLI Arguments
| Argument | Description | Default |
|----------|-------------|---------|
| `--video` | Input video path | *Required* |
| `--output-csv` | CSV output path | `../../data/detections/detections.csv` |
| `--output-patches` | ROI patches directory | `../../data/roi_patches` |
| `--model` | YOLOv8 weights path | `yolov8n.pt` (auto-download) |
| `--device` | Inference device | `mps` (M4), `cuda` (GPU), `cpu` |
| `--conf` | Confidence threshold | `0.25` |
| `--sample-fps` | Sampling rate | `1` FPS |

### Hardware-Specific Settings

**M4 MacBook Pro** (recommended):
```bash
--device mps --sample-fps 1
```

**NVIDIA GPU**:
```bash
--device cuda --sample-fps 2
```

**CPU Only** (slow):
```bash
--device cpu --sample-fps 1
```

---

## Performance Benchmarks

### M4 MacBook Pro (MPS)
- **Inference Time**: ~10ms per frame
- **Throughput**: ~96 FPS (processing speed)
- **Real-time Factor**: 96× faster than real-time (30 FPS video)
- **Memory**: ~2GB GPU, ~500MB RAM

### Expected Production Metrics
- **Dataset**: 256GB video (~100 hours at 30 FPS)
- **Frames**: ~10.8M total frames
- **Sampled**: ~360K frames at 1 FPS
- **Detections**: ~500K (estimated at 1.4 detections/frame)
- **Processing Time**: ~62 minutes on M4

---

## GPS Extraction (TODO)

### Current: Simulated GPS
```python
def extract_gps_from_frame(self, frame, frame_number):
    # Simulated drift for testing
    base_lat = 43.7900
    base_lon = -79.3140
    lat = base_lat + (frame_number / 10000) * 0.0001
    lon = base_lon + (frame_number / 10000) * 0.0001
    return lat, lon, heading
```

### Planned: OCR-Based Extraction
```python
import pytesseract
from PIL import Image

def extract_gps_from_frame(self, frame, frame_number):
    # Crop overlay region (bottom-left corner)
    h, w = frame.shape[:2]
    overlay = frame[h-50:h, 0:300]  # Adjust based on overlay position
    
    # Run OCR
    text = pytesseract.image_to_string(Image.fromarray(overlay))
    
    # Parse "N43.7900 W79.3140" format
    lat, lon = parse_gps_text(text)
    heading = extract_heading_from_imu()  # Requires IMU data
    
    return lat, lon, heading
```

---

## Integration with Module B

### Workflow
```
Module A (Perception)          Module B (Ingestion)
=====================          ====================
Video → YOLOv8 Detection
     → GPS Extraction
     → ROI Extraction
     → CSV Generation  →  →  →  CSV Reader (Go)
                              → Kafka Producer
                              → Confluent Cloud
```

### Data Handoff
1. **Perception** writes CSV to `../../data/detections/`
2. **Ingestion** reads CSV via `ingestion/csv_reader.go`
3. **Ingestion** streams to Kafka topic `sentinel_map_detections`

### Run Full Pipeline
```bash
# Step 1: Generate detections (Module A)
cd modules/perception
python detect_and_extract.py --video ../../data/videos/dashcam_001.mp4

# Step 2: Ingest to Kafka (Module B)
cd ../ingestion
./bin/producer -csv ../../data/detections/detections.csv -vehicle vehicle-001
```

---

## Project Structure

```
modules/perception/
├── detect_and_extract.py    # Main detection script
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── venv/                     # Virtual environment (gitignored)
└── yolov8n.pt               # YOLOv8 weights (auto-downloaded)
```

---

## Development Roadmap

- [x] YOLOv8 detection with M4 MPS acceleration
- [x] ROI patch extraction (256×256)
- [x] CSV output with GPS fields
- [x] Configurable sampling rate
- [ ] OCR-based GPS extraction from overlays
- [ ] Multi-video batch processing
- [ ] Real-time streaming mode (webcam/RTSP)
- [ ] Detection quality metrics (precision/recall)
- [ ] ROI patch compression (JPEG → WebP)

---

## Related Documentation

- [Module B (Ingestion)](../ingestion/README.md)
- [Project Overview](../../README.md)
- [Production Specs](../../docs/prod-pipeline-specs-en.md)
- [YOLOv8 Docs](https://docs.ultralytics.com/)
