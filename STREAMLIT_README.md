# Traffic Sign Mapping Dashboard - Quick Start

## Streamlit App is Running! 🎉

The dashboard is now accessible at: **http://localhost:8501**

## Features

### 📹 Video Playback
- Displays the processed dashcam video
- Located in the left column

### 🗺️ Interactive Map
- Shows all 4 OSM traffic signs on an interactive map
- Red markers indicate OSM ground truth locations
- Click markers for details (ID, type, coordinates)

### 📊 Sidebar Statistics
- **Total Detections**: 473
- **OSM Ground Truth**: 4 traffic signs
- **Detection Breakdown**: Stop signs & traffic lights
- **Audit Status**: Verified, New, Missing counts

### 📈 Analytics
- Detection statistics over time
- Confidence distribution by class
- Frame-by-frame detection timeline
- Interactive data filtering

### 📋 Data Export
- Filter detections by class and confidence
- Download filtered data as CSV

### ⚠️ System Limitations
The dashboard includes a section covering:
1. **Camera Calibration** - Current state and improvements needed
2. **Multi-frame Fusion** - Tracking and merging detections
3. **Real-time GPS Integration** - GPS/IMU fusion requirements

## How to Use

1. **Open your browser** to http://localhost:8501
2. **Explore the sidebar** for quick statistics
3. **Watch the video** on the left side
4. **View the map** showing OSM traffic sign locations
5. **Scroll down** for detailed analytics and charts
6. **Filter data** using the controls above the data table
7. **Download** filtered detection data as needed

## To Stop the App

Press `Ctrl+C` in the terminal where Streamlit is running, or close the terminal.

## Files Used

- `traffic_signs.csv` - 473 YOLO detections
- `osm.xml` - 4 OSM ground truth signs  
- `vid_input.mp4` - Dashcam video
- `real_comparison_results.csv` - Comparison results (if available)

---

**Enjoy exploring your traffic sign mapping project! 🚦**
