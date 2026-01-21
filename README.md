# SentinelMap: Automated Traffic Sign Geolocation System

A production-grade geospatial mapping pipeline that processes dashcam footage to detect, geolocate, and map traffic infrastructure at scale.

**Inspired by**: Lyft's Level 5 Mapping Platform  
**Goal**: Automate map auditing using computer vision + GPS telemetry + cloud analytics

---

## 🎯 Project Overview

SentinelMap transforms raw dashcam footage into actionable map intelligence:

```
📹 256GB Video Footage
    ↓
🤖 Module A: Perception Layer (YOLOv8 Detection + GPS Extraction)
    ↓
📊 CSV Detections (500K records)
    ↓
🚀 Module B: Ingestion Layer (Golang Kafka Producer)
    ↓
☁️  Confluent Cloud Kafka (Stream Processing)
    ↓
❄️  Snowflake Warehouse (Geospatial Analytics)
    ↓
🗺️  Automated Map Updates
```

---

## 📂 Project Structure

```
geospatial-mapping-demo/
├── modules/
│   ├── perception/              # Module A: YOLOv8 Detection (Python)
│   │   ├── detect_and_extract.py  # Main detection pipeline
│   │   ├── requirements.txt       # Python dependencies
│   │   └── README.md              # Perception layer docs
│   │
│   └── ingestion/               # Module B: Kafka Producer (Go)
│       ├── cmd/                   # CLI applications
│       ├── config/                # Kafka configuration
│       ├── models/                # Data models
│       ├── producer/              # Producer logic
│       ├── ingestion/             # CSV streaming
│       ├── Makefile               # Build commands
│       └── README.md              # Ingestion layer docs
│
├── data/                        # Shared data directory
│   ├── videos/                    # Input: dashcam footage
│   ├── detections/                # Output: CSV detection files
│   └── roi_patches/               # Output: 256×256 ROI images
│
├── docs/                        # Documentation
│   ├── prod-pipeline-specs-en.md  # Architecture specs
│   └── CONFLUENT_SETUP.md         # Kafka setup guide
│
├── local-mvp/                   # Proof-of-concept (reference only)
│   ├── traffic_sign_detection/
│   ├── streamlit_app.py
│   └── README.md
│
└── README.md                    # This file
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+** (for perception layer)
- **Go 1.20+** (for ingestion layer)
- **Confluent Cloud account** (free $400 credits)
- **M4 MacBook Pro** (or CUDA-enabled GPU)

### Setup

#### 1. Clone Repository
```bash
git clone <repo-url>
cd geospatial-mapping-demo
```

#### 2. Set Up Module A (Perception)
```bash
cd modules/perception

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download YOLOv8 weights (auto-downloaded on first run)
```

#### 3. Set Up Module B (Ingestion)
```bash
cd modules/ingestion

# Install Go dependencies
make deps

# Configure Kafka credentials
cp .env.example .env
# Edit .env with your Confluent Cloud settings

# Build binaries
make build
```

---

## 🎬 Usage

### End-to-End Pipeline

#### Step 1: Generate Detections (Module A)
```bash
cd modules/perception

python detect_and_extract.py \
  --video ../../data/videos/20260118191513_035087.MP4 \
  --output-csv ../../data/detections/detections.csv \
  --output-patches ../../data/roi_patches \
  --sample-fps 1 \
  --device mps
```

**Output**:
- `data/detections/detections.csv` (58 detections)
- `data/roi_patches/frame_*.jpg` (58 ROI images, 256×256)
- Processing time: 16.49s for 563MB video

#### Step 2: Stream to Kafka (Module B)
```bash
cd modules/ingestion

./bin/producer \
  -csv ../../data/detections/detections.csv \
  -vehicle vehicle-001 \
  -workers 20 \
  -session session-$(date +%Y%m%d)
```

**Output**:
```
📊 Metrics - Sent: 58 | Acked: 58 | Failed: 0
⏱️  Total Time: 782ms
🚀 Throughput: 74.17 messages/sec
✅ Success Rate: 100.00%
```

---

## 📊 Data Flow

### CSV Schema (Module A → Module B)
```csv
frame_number,timestamp_sec,u,v,confidence,class_name,vehicle_lat,vehicle_lon,heading
75,2.500,1737.28,630.06,0.5249,stop sign,43.7900,-79.3140,45.0
185,6.167,2141.59,200.01,0.3381,traffic light,43.7905,-79.3138,47.5
```

### Kafka JSON (Module B → Cloud)
```json
{
  "detection_id": "550e8400-e29b-41d4-a716-446655440000",
  "vehicle_id": "vehicle-001",
  "session_id": "20260119-abc123",
  "ingested_at": "2026-01-19T10:30:45Z",
  "frame_number": 75,
  "timestamp_sec": 2.5,
  "pixel_u": 1737.28,
  "pixel_v": 630.06,
  "confidence": 0.5249,
  "class_name": "stop sign",
  "vehicle_lat": 43.7900,
  "vehicle_lon": -79.3140,
  "heading": 45.0
}
```

---

## 🏗️ Architecture

### Module A: Perception Layer (Python)
**Purpose**: Extract traffic sign detections from video

**Key Features**:
- YOLOv8 object detection (stop signs, traffic lights)
- M4 MPS hardware acceleration (~96 FPS inference)
- GPS extraction from frame overlays (OCR planned)
- 256×256 ROI patch extraction
- CSV output for downstream ingestion

**Technology**: Python, ultralytics, OpenCV, PyTorch

[📖 Module A Documentation](modules/perception/README.md)

---

### Module B: Ingestion Layer (Golang)
**Purpose**: Stream detections to Kafka with high throughput

**Key Features**:
- Goroutine-based parallelism (10-50 workers)
- Exponential backoff retry (5 attempts)
- Idempotent producer (exactly-once semantics)
- Real-time metrics (TPS, success rate)
- CSV streaming (1.7M records/sec parse rate)

**Technology**: Go, confluent-kafka-go, goroutines

[📖 Module B Documentation](modules/ingestion/README.md)

---

### Module C: Data Modeling (Snowflake)
**Purpose**: Store and validate detections against OSM ground truth

**Key Features**:
- Snowpipe Streaming (real-time ingestion from Kafka)
- VARIANT JSON storage with flexible schema
- Spatial queries with GEOGRAPHY type (ST_DISTANCE)
- 51,556 OSM nodes for Toronto traffic infrastructure
- Proximity matching with configurable thresholds

**Technology**: Snowflake, SQL, Snowpipe Streaming, GEOGRAPHY

[📖 Module C Documentation](modules/data-modeling/README.md)

---

### Module D: Analytics Layer (dbt Cloud)
**Purpose**: Transform raw data into actionable insights with data quality validation

**Key Features**:
- 3-layer architecture (staging → core → marts)
- Spatial audit with ST_DISTANCE joins (10m threshold)
- Automated classification (VERIFIED, CLASS_MISMATCH, NEW_DISCOVERY)
- 16 data quality tests (100% pass rate)
- Daily aggregations with verification rates
- Prioritized review queue (HIGH/MEDIUM/LOW)

**Technology**: dbt Core, Snowflake, SQL, Python

[📖 Module D Documentation](analytics/README.md)

---

## 📈 Performance Metrics

### Module A: Perception
| Metric | Value |
|--------|-------|
| Inference Time | ~45ms per frame |
| Throughput | ~11 FPS (M4 MPS) |
| Real-time Factor | 11× faster than real-time |
| Memory Usage | ~2GB GPU, ~500MB RAM |

**Latest Test** (563MB video, 5,400 frames):
- Processed 180 frames @ 1 FPS sampling
- Found 58 traffic light detections
- Processing time: 16.49s (10.92 FPS avg)

### Module B: Ingestion
| Metric | Value |
|--------|-------|
| Parse Rate | 144K records/sec |
| Kafka Throughput | 74-587 msg/sec (tested) |
| Success Rate | 100% (with retry) |
| Latency (P99) | <100ms |

**Latest Test** (58 detections → Kafka):
- Messages sent: 58, Acked: 58, Failed: 0
- Throughput: 74.17 msg/sec
- Total time: 782ms
- Success rate: 100%

### Expected Production Scale
- **Input**: 256GB video (~100 hours at 30 FPS)
- **Frames**: 10.8M total, 360K sampled (1 FPS)
- **Detections**: ~500K (1.4 per frame avg)
- **Processing Time**: ~62 minutes on M4

---

## 🧪 Testing

### Module A: Perception (Local Testing)
```bash
cd modules/perception

# Process sample video
python detect_and_extract.py \
  --video ../../local-mvp/sample_dashcam.mp4 \
  --output-csv /tmp/test_detections.csv \
  --conf 0.25
```

### Module B: Ingestion (Dry-Run Without Kafka)
```bash
cd modules/ingestion

# Test CSV parsing only
make dry-run

# Expected output:
# ✅ Total Records Parsed: 473
# ⏱️  Parse Time: 270µs
# 🚀 Parse Rate: 1,755,102 records/sec
```

### Module B: Unit Tests
```bash
cd modules/ingestion
make test

# Expected:
# PASS: models/detection_test.go (100% coverage)
# PASS: ingestion/csv_reader_test.go
```

---

## 🔧 Configuration

### Environment Variables (Module B)
Create `modules/ingestion/.env`:

```bash
KAFKA_BOOTSTRAP_SERVERS=pkc-xxxxx.us-east-1.aws.confluent.cloud:9092
KAFKA_SASL_USERNAME=your-api-key
KAFKA_SASL_PASSWORD=your-api-secret
KAFKA_TOPIC=sentinel_map_detections
KAFKA_COMPRESSION_TYPE=snappy
KAFKA_BATCH_SIZE=16384
```

[📖 Confluent Cloud Setup Guide](docs/CONFLUENT_SETUP.md)

---

## 📚 Documentation

- **[Module A (Perception)](modules/perception/README.md)** - YOLOv8 detection pipeline
- **[Module B (Ingestion)](modules/ingestion/README.md)** - Kafka producer
- **[Module C (Data Modeling)](modules/data-modeling/README.md)** - Snowflake setup
- **[Module D (Analytics)](analytics/README.md)** - dbt transformation layer
- **[Production Specs](docs/prod-pipeline-specs-en.md)** - Architecture details
- **[Confluent Setup](docs/CONFLUENT_SETUP.md)** - Kafka configuration
- **[Local MVP](local-mvp/README.md)** - Proof-of-concept reference

---

## 🛣️ Roadmap

### Completed ✅
- [x] Local MVP (Streamlit app with OSM integration)
- [x] Module A: YOLOv8 detection with M4 MPS acceleration
- [x] Module A: ROI patch extraction (256×256)
- [x] Module A: OCR-based GPS extraction from VIOFO A119 V3 overlay
- [x] Module A: Recording timestamp extraction (DD/MM/YYYY HH:MM:SS)
- [x] Module B: Golang Kafka producer with goroutines
- [x] Module B: CSV streaming with GPS + timestamp support
- [x] Module B: Exponential backoff + idempotent writes
- [x] Module C: Snowflake database setup with resource monitoring
- [x] Module C: Kafka-Snowflake connector (Snowpipe Streaming)
- [x] Module C: OSM ground truth ingestion (51,556 Toronto nodes)
- [x] Module C: Spatial proximity matching (ST_DISTANCE queries)
- [x] Module D: dbt analytics layer (staging → core → marts)
- [x] Module D: Spatial audit with 10m verification threshold
- [x] Module D: Data quality tests (16 tests, 100% pass rate)
- [x] Module D: Batch processing (90 detections from 10 videos)
- [x] Confluent Cloud integration (100% success rate)
- [x] End-to-end testing (90 detections processed through full pipeline)
- [x] Modular architecture (perception → ingestion → modeling → analytics)
- [x] Comprehensive documentation (READMEs + SQL + dbt models + troubleshooting)

### In Progress 🚧
- [ ] Production benchmarking (256GB dataset)

### Planned 📋
- [ ] Automated map diff generation (OSM comparison)
- [ ] Real-time dashboard (detection heatmap)
- [ ] H3/S2 spatial indexing for faster joins
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Time-series analysis (detection trends)

---

## 🤝 Contributing

This is a portfolio project demonstrating production-grade data engineering skills. Contributions welcome!

**Key Areas**:
- OCR integration for GPS extraction
- Multi-GPU training for YOLOv8 fine-tuning
- Snowflake geospatial queries
- Performance optimization

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- **Lyft Level 5**: Inspiration for mapping pipeline
- **Ultralytics**: YOLOv8 object detection framework
- **Confluent**: Kafka cloud platform
- **Snowflake**: Data warehousing

---

## 📬 Contact

**Author**: Boyang Li  
**Email**: bryanli2009@live.ca  
**LinkedIn**: [linkedin.com/in/boyang419](https://www.linkedin.com/in/boyang419/)

---

**Built with**: Python, Go, YOLOv8, Kafka, Confluent Cloud, Snowflake
