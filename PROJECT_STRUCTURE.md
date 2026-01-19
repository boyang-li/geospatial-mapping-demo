# Traffic Sign Mapping Project

## Project Overview

This project implements an end-to-end pipeline for detecting, mapping, and validating traffic signs from dashcam video footage. Using YOLOv8 for computer vision-based object detection, the system processes video frames to identify traffic signs, converts pixel coordinates to real-world GPS locations using camera geometry and vehicle positioning, and validates detections against OpenStreetMap (OSM) ground truth data. The workflow includes: (1) video processing with YOLOv8 to extract traffic sign detections and pixel coordinates, (2) geometric transformation from 2D image coordinates to 3D world distances using camera parameters, (3) GPS coordinate calculation using vehicle position and heading data, (4) comparison with OSM ground truth to verify accuracy and identify new or missing signs, and (5) interactive visualization through a Streamlit dashboard that displays detection statistics, temporal analysis, geographic mapping, and audit results.

### Streamlit App Workflow

The dashboard (`streamlit_app.py`) provides an interactive web interface to explore the mapping results:

1. **Data Loading**: Loads detection results from CSV (`traffic_signs.csv`), OSM ground truth from XML (`osm.xml`), and comparison results
2. **Unique Sign Estimation**: Applies spatial-temporal clustering to group frame-by-frame detections into unique sign estimates (within 100 frames, 200px horizontal, 100px vertical)
3. **Visualization Layers**:
   - Video playback with synchronized detection timeline (time slider to scrub through video)
   - Interactive Folium map showing OSM ground truth markers
   - Summary metrics: estimated unique signs, frames analyzed, OSM count, audit status
   - Detection statistics: confidence distributions, temporal patterns, class breakdowns
4. **Audit Interface**: Displays verified, new, and missing signs from GPS comparison
5. **Data Export**: Provides filtered detection data download capability

---

## Project Structure

```
Mapping/
├── traffic_sign_detection/
│   ├── detect_traffic_signs.py
│   ├── vid_input.mp4
│   └── yolov8n.pt
├── __pycache__/
├── camera-info.txt
├── Camera Intrinsics
├── osm.xml
├── overpass-query.ql
├── vid_frame.txt
├── vid_frame.png
├── pixel_to_distance.py
├── get_object_gps.py
├── compare_gps.py
├── simulated_test_comparison.py
├── real_data_comparison.py
├── traffic_signs.csv
├── comparison_results.csv
├── simulated_comparison_results.csv
├── real_comparison_results.csv
├── streamlit_app.py
├── streamlit_app_backup.py
├── STREAMLIT_README.md
├── PROJECT_STRUCTURE.md
├── 20260118191513_035087.MP4
├── 71fOFkbtcML._AC_SX679_.jpg
├── Latitude-and-Longitude.png
└── .DS_Store
```

---

## File Descriptions

### Core Detection Module

#### `traffic_sign_detection/detect_traffic_signs.py`
- **Type**: Python Script
- **Description**: Main YOLOv8 detection script that processes video files frame-by-frame to identify traffic signs (stop signs and traffic lights). Extracts bottom-center pixel coordinates (u, v) where u = (x1+x2)/2 and v = y2 for each detection. Outputs frame number, timestamp, pixel coordinates, confidence score, and class name to CSV. Supports `--all` flag to detect all COCO classes.

#### `traffic_sign_detection/vid_input.mp4`
- **Type**: Video File (MP4)
- **Description**: Input dashcam video footage (1440p resolution, 30 FPS, 92° vertical FOV) used for traffic sign detection. Contains approximately 32 seconds of driving footage with multiple traffic sign appearances.

#### `traffic_sign_detection/yolov8n.pt`
- **Type**: Model Weights (PyTorch)
- **Description**: Pre-trained YOLOv8 nano model weights from Ultralytics. Trained on COCO dataset with 80 object classes including 'stop sign' and 'traffic light'. Used for real-time object detection inference.

---

### Coordinate Transformation & GPS Modules

#### `pixel_to_distance.py`
- **Type**: Python Module
- **Description**: Converts vertical pixel coordinates (v) to real-world ground distance using camera geometry. Implements pinhole camera model with parameters: image height H=1440px, camera height h=1.4m, vertical FOV=92°, horizon at v=720px (camera parallel to ground). Uses arctangent to calculate viewing angle and trigonometry to compute distance. Returns infinity for pixels above horizon line.

#### `get_object_gps.py`
- **Type**: Python Module
- **Description**: Calculates GPS coordinates of detected objects using vehicle position, heading, and distance. Implements inverse Haversine formula for great circle navigation on Earth sphere (R=6371000m). Takes vehicle latitude/longitude, heading in degrees (0°=North), and distance in meters, returns target object's GPS coordinates as (lat, lon) tuple.

---

### GPS Comparison & Validation

#### `compare_gps.py`
- **Type**: Python Module
- **Description**: Core validation module that compares detected traffic sign GPS coordinates against OpenStreetMap ground truth data. Includes three main functions: (1) `parse_osm_xml()` - parses OSM XML files to extract traffic signs with specific tags, supports wildcard tag values, (2) `haversine_distance()` - calculates great circle distance between GPS coordinates in meters, (3) `compare_gps_lists()` - performs bidirectional comparison with configurable thresholds (verify_threshold=10m, missing_threshold=15m), outputs verified, new, and missing sign lists.

#### `simulated_test_comparison.py`
- **Type**: Python Script
- **Description**: Unit test script with hardcoded GPS coordinates to validate the comparison logic. Tests the complete workflow using simulated detected signs and OSM ground truth. Demonstrates proper functioning of verification, new sign detection, and missing sign identification. Results: 2 verified, 1 new, 2 missing signs.

#### `real_data_comparison.py`
- **Type**: Python Script
- **Description**: Production pipeline script that integrates all components. Loads actual detections from `traffic_signs.csv`, parses OSM data from `osm.xml`, applies simulated vehicle GPS (43.7900°N, -79.3140°W with 0° heading), uses fixed distance=30m for all detections (since all are above horizon line), generates `real_comparison_results.csv` with status labels (Verified/New Sign Detected/Missing Sign on Road).

---

### Data Files

#### `traffic_signs.csv`
- **Type**: CSV Data
- **Description**: Detection results containing 473 rows of frame-by-frame traffic sign detections. Columns: frame_number, timestamp_sec, u (horizontal pixel), v (vertical pixel), confidence (0-1), class_name (stop sign/traffic light). Generated by `detect_traffic_signs.py` from processing `vid_input.mp4` over 954 frames (31.8 seconds).

#### `osm.xml`
- **Type**: XML Data (OpenStreetMap)
- **Description**: OpenStreetMap export containing ground truth traffic sign data for the Toronto area. Includes 4 traffic signs with tag k="traffic_sign" v="maxspeed". Each node contains id, latitude, longitude, and metadata tags. Downloaded via Overpass API query defined in `overpass-query.ql`.

#### `comparison_results.csv`
- **Type**: CSV Data
- **Description**: Output from GPS comparison showing matched and unmatched traffic signs with distance calculations and verification status.

#### `simulated_comparison_results.csv`
- **Type**: CSV Data
- **Description**: Test output from `simulated_test_comparison.py` demonstrating the comparison algorithm with synthetic data.

#### `real_comparison_results.csv`
- **Type**: CSV Data
- **Description**: Production comparison results from `real_data_comparison.py` showing 473 new signs detected, 0 verified, and 4 missing OSM signs. Uses simulated vehicle GPS due to lack of real-time positioning data.

---

### Configuration & Reference Files

#### `camera-info.txt`
- **Type**: Text Configuration
- **Description**: Camera specifications and calibration parameters. Contains image resolution (1440p), vertical field of view (92°), camera mounting height (1.4m), and orientation (parallel to ground). Used by `pixel_to_distance.py` for geometric calculations.

#### `Camera Intrinsics`
- **Type**: Text File
- **Description**: Detailed camera intrinsic parameters documentation, potentially including focal length, principal point, and lens distortion coefficients for advanced calibration.

#### `overpass-query.ql`
- **Type**: Overpass QL Script
- **Description**: Overpass API query script used to download traffic sign data from OpenStreetMap. Defines geographic bounding box and tag filters (node["traffic_sign"]) for extracting relevant POI data. Used to generate `osm.xml`.

#### `vid_frame.txt`
- **Type**: Text File
- **Description**: Metadata or annotation file containing information about specific video frames, possibly frame numbers of interest or manual annotations.

#### `vid_frame.png`
- **Type**: Image File (PNG)
- **Description**: Sample frame extracted from the video for reference, testing, or documentation purposes. May show example detections or camera view geometry.

---

### Visualization & Dashboard

#### `streamlit_app.py`
- **Type**: Python Web Application (Streamlit)
- **Description**: Interactive dashboard for visualizing traffic sign mapping results. Features include: (1) Video player with synchronized detection timeline using time slider, (2) Folium interactive map displaying OSM ground truth markers, (3) Sidebar metrics showing estimated unique signs (via clustering), frames analyzed, audit status, (4) Detection statistics with confidence histograms and temporal line charts, (5) Filterable data table with CSV export, (6) System limitations documentation (camera calibration, multi-frame fusion, GPS integration needs). Runs on http://localhost:8501.

#### `streamlit_app_backup.py`
- **Type**: Python Script (Backup)
- **Description**: Backup copy of previous version of Streamlit app created before major refactoring. Contains earlier implementation before adding unique sign clustering and timeline features.

#### `STREAMLIT_README.md`
- **Type**: Markdown Documentation
- **Description**: README file with instructions for running the Streamlit dashboard, including installation commands, usage guidelines, and feature descriptions.

---

### Media & Reference Materials

#### `20260118191513_035087.MP4`
- **Type**: Video File (MP4)
- **Description**: Additional dashcam footage, possibly raw unprocessed video or alternative test footage for the mapping system.

#### `71fOFkbtcML._AC_SX679_.jpg`
- **Type**: Image File (JPEG)
- **Description**: Reference image, likely product photo of the dashcam hardware used for video capture or documentation illustration.

#### `Latitude-and-Longitude.png`
- **Type**: Image File (PNG)
- **Description**: Diagram or illustration explaining latitude/longitude coordinate system, GPS calculations, or geographic reference for the Haversine formula implementation.

---

### System Files

#### `__pycache__/`
- **Type**: Directory (Python Cache)
- **Description**: Python bytecode cache directory containing compiled `.pyc` files for faster module loading. Auto-generated by Python interpreter for imported modules.

#### `.DS_Store`
- **Type**: System File (macOS)
- **Description**: macOS Finder metadata file storing folder view preferences, icon positions, and display settings. Can be safely ignored or added to `.gitignore`.

#### `PROJECT_STRUCTURE.md`
- **Type**: Markdown Documentation
- **Description**: This file. Comprehensive project documentation including overview, workflow description, file tree structure, and detailed descriptions of all project files.

---

## Technology Stack

- **Computer Vision**: Ultralytics YOLOv8 (COCO pre-trained model)
- **Video Processing**: OpenCV (cv2)
- **Geospatial**: Haversine formula, OSM XML parsing (ElementTree)
- **Web Dashboard**: Streamlit, Folium, streamlit-folium
- **Data Processing**: Pandas, NumPy
- **Python**: 3.12 (Conda environment)
- **Dependencies**: ultralytics, opencv-python, streamlit, folium, streamlit-folium, pandas, numpy

---

## Workflow Summary

```
Video Input (vid_input.mp4)
    ↓
YOLOv8 Detection (detect_traffic_signs.py)
    ↓
Pixel Coordinates (traffic_signs.csv)
    ↓
Geometric Transform (pixel_to_distance.py)
    ↓
GPS Calculation (get_object_gps.py)
    ↓
OSM Comparison (compare_gps.py)
    ↓
Results & Visualization (streamlit_app.py)
```

**Key Metrics**: 473 total detections → ~39 estimated unique signs (via clustering) → 0 verified, 473 new, 4 missing (with simulated GPS)
