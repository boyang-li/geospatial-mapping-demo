#!/usr/bin/env python3
"""
Traffic Sign Mapping Dashboard
A Streamlit app to visualize detected traffic signs and OSM ground truth.
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import sys
sys.path.insert(0, '/Users/boyangli/Repo/Mapping')

from compare_gps import parse_osm_xml, osm_nodes_to_coordinates

# Page configuration
st.set_page_config(
    page_title="Traffic Sign Mapping Dashboard",
    page_icon="🚦",
    layout="wide"
)

# Title
st.title("🚦 Traffic Sign Mapping & Validation Dashboard")
st.markdown("---")

# Load data
@st.cache_data
def load_detections():
    """Load detected traffic signs from CSV."""
    df = pd.read_csv('/Users/boyangli/Repo/Mapping/traffic_signs.csv')
    return df

@st.cache_data
def load_osm_data():
    """Load OSM ground truth data."""
    osm_nodes = parse_osm_xml('/Users/boyangli/Repo/Mapping/osm.xml', 'traffic_sign', None)
    return osm_nodes

@st.cache_data
def load_comparison_results():
    """Load comparison results if available."""
    try:
        df = pd.read_csv('/Users/boyangli/Repo/Mapping/real_comparison_results.csv')
        return df
    except FileNotFoundError:
        return None

def estimate_unique_signs(df):
    """Rough estimate of unique signs by grouping nearby detections."""
    unique_count = 0
    processed = set()
    
    for idx, row in df.iterrows():
        if idx in processed:
            continue
        
        # Find all detections of same class within 100 frames and similar position
        similar = df[
            (df['class_name'] == row['class_name']) &
            (abs(df['frame_number'] - row['frame_number']) < 100) &
            (abs(df['u'] - row['u']) < 200) &  # Similar horizontal position
            (abs(df['v'] - row['v']) < 100)    # Similar vertical position
        ]
        
        processed.update(similar.index)
        unique_count += 1
    
    return unique_count

# Load all data
detections_df = load_detections()
osm_nodes = load_osm_data()
comparison_df = load_comparison_results()
unique_signs = estimate_unique_signs(detections_df)

# Sidebar - Summary Statistics
st.sidebar.header("📊 Project Summary")

st.sidebar.metric("Estimated Unique Signs", unique_signs)
st.sidebar.metric("Frames Analyzed", detections_df['frame_number'].nunique())
st.sidebar.metric("OSM Ground Truth", len(osm_nodes))

# Detection breakdown by class
st.sidebar.subheader("Detection Breakdown")
class_counts = detections_df['class_name'].value_counts()
for class_name, count in class_counts.items():
    st.sidebar.write(f"- {class_name}: {count} instances")

# Audit status
st.sidebar.subheader("🔍 Audit Status")
if comparison_df is not None:
    verified = len(comparison_df[comparison_df['Status'] == 'Verified'])
    new_signs = len(comparison_df[comparison_df['Status'] == 'New Sign Detected'])
    missing = len(comparison_df[comparison_df['Status'] == 'Missing Sign on Road'])
    
    st.sidebar.metric("✅ Verified", verified)
    st.sidebar.metric("⚠️ New Signs", new_signs)
    st.sidebar.metric("❌ Missing", missing)
else:
    st.sidebar.info("Run comparison to see audit status")

st.sidebar.markdown("---")
st.sidebar.caption("Built with YOLOv8 + OSM + Streamlit")

# Main content - Two columns
col1, col2 = st.columns([1, 1])

# Left column - Video
with col1:
    st.header("📹 Processed Video")
    
    # Check if video file exists
    import os
    video_paths = [
        '/Users/boyangli/Repo/Mapping/traffic_sign_detection/vid_input.mp4',
        '/Users/boyangli/Repo/Mapping/vid_input.mp4'
    ]
    
    video_path = None
    for path in video_paths:
        if os.path.exists(path):
            video_path = path
            break
    
    if video_path:
        st.video(video_path)
        st.caption(f"Video: {os.path.basename(video_path)}")
    else:
        st.warning("Video file not found. Please ensure vid_input.mp4 is in the project directory.")
    
    # Real-time Detection Display
    st.subheader("🔍 Current Detections")
    
    # Time slider to navigate through video
    max_time = detections_df['timestamp_sec'].max()
    current_time = st.slider(
        "Video Time (seconds)",
        min_value=0.0,
        max_value=float(max_time),
        value=0.0,
        step=0.1,
        key="video_time"
    )
    
    # Find frame at current time
    current_frame = int(current_time * 30)  # 30 FPS
    
    # Get detections within 0.5 second window
    time_window = 0.5
    nearby_detections = detections_df[
        (detections_df['timestamp_sec'] >= current_time - time_window) &
        (detections_df['timestamp_sec'] <= current_time + time_window)
    ]
    
    # Display current state
    if len(nearby_detections) > 0:
        st.success(f"**Frame {current_frame}** | Time: {current_time:.2f}s")
        st.write("**Objects Detected:**")
        
        # Group by class and show counts
        class_counts = nearby_detections['class_name'].value_counts()
        for class_name, count in class_counts.items():
            avg_conf = nearby_detections[nearby_detections['class_name'] == class_name]['confidence'].mean()
            st.write(f"- **{class_name}**: {count} detection(s) (avg confidence: {avg_conf:.1%})")
    else:
        st.info(f"**Frame {current_frame}** | Time: {current_time:.2f}s")
        st.write("No objects detected at this time")
    
    st.caption("💡 Move the slider to see detections at different points in the video")

# Right column - Map
with col2:
    st.header("🗺️ Traffic Sign Locations")
    
    if osm_nodes:
        # Create map centered on OSM points
        osm_coords = osm_nodes_to_coordinates(osm_nodes)
        avg_lat = sum(lat for lat, lon in osm_coords) / len(osm_coords)
        avg_lon = sum(lon for lat, lon in osm_coords) / len(osm_coords)
        
        # Create folium map
        m = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=14,
            tiles='OpenStreetMap'
        )
        
        # Add OSM points as markers
        for i, node in enumerate(osm_nodes, 1):
            folium.Marker(
                location=[node['lat'], node['lon']],
                popup=f"OSM Sign {i}<br>Type: {node.get('type', 'N/A')}<br>ID: {node['id']}",
                tooltip=f"OSM Sign {i}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        
        # Display map
        st_folium(m, width=700, height=500)
        
        # Display table
        st.subheader("OSM Traffic Signs")
        osm_df = pd.DataFrame(osm_nodes)
        osm_df = osm_df[['id', 'type', 'lat', 'lon']]
        st.dataframe(osm_df, use_container_width=True)
    else:
        st.warning("No OSM data found.")

# Detection Statistics
st.markdown("---")
st.header("📈 Detection Statistics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Estimated Unique Signs", unique_signs)
    st.caption("Clustered from all detections")
    
with col2:
    st.metric("Total Detection Instances", len(detections_df))
    st.caption("Across all video frames")

with col3:
    st.metric("Frames with Detections", detections_df['frame_number'].nunique())
    st.caption(f"Out of {detections_df['frame_number'].max()} total frames")

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Video Duration", f"{detections_df['timestamp_sec'].max():.1f} sec")
    st.metric("Video FPS", "30")

with col2:
    st.metric("Avg Confidence", f"{detections_df['confidence'].mean():.2%}")
    st.metric("Min/Max Confidence", f"{detections_df['confidence'].min():.2%} / {detections_df['confidence'].max():.2%}")

with col3:
    avg_detections_per_sign = len(detections_df) / unique_signs if unique_signs > 0 else 0
    st.metric("Avg Frames per Sign", f"{avg_detections_per_sign:.1f}")
    st.caption("How long each sign appears")

# Confidence distribution chart
st.subheader("Confidence Distribution by Class")
import numpy as np
for class_name in detections_df['class_name'].unique():
    class_df = detections_df[detections_df['class_name'] == class_name]
    st.write(f"**{class_name}** (n={len(class_df)})")
    
    # Create histogram data with proper bin labels
    bins = np.linspace(0, 1, 11)
    hist_data, bin_edges = np.histogram(class_df['confidence'], bins=bins)
    bin_labels = [f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}" for i in range(len(bin_edges)-1)]
    hist_df = pd.DataFrame({'Range': bin_labels, 'Count': hist_data}).set_index('Range')
    st.bar_chart(hist_df)

# Detections over time
st.subheader("Detections Over Time")
detections_df['time_bin'] = pd.cut(detections_df['timestamp_sec'], bins=20)
time_counts = detections_df.groupby(['time_bin', 'class_name']).size().unstack(fill_value=0)
# Convert interval index to string for display
time_counts.index = time_counts.index.astype(str)
st.line_chart(time_counts)

# Detection Data Table
st.markdown("---")
st.header("📋 Detection Data")

# Filters
col1, col2 = st.columns(2)
with col1:
    selected_class = st.multiselect(
        "Filter by Class",
        options=detections_df['class_name'].unique(),
        default=detections_df['class_name'].unique()
    )
with col2:
    min_confidence = st.slider(
        "Minimum Confidence",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05
    )

# Filter data
filtered_df = detections_df[
    (detections_df['class_name'].isin(selected_class)) &
    (detections_df['confidence'] >= min_confidence)
]

st.write(f"Showing {len(filtered_df)} of {len(detections_df)} detections")
st.dataframe(filtered_df, use_container_width=True)

# Download button
csv = filtered_df.to_csv(index=False)
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=csv,
    file_name="filtered_detections.csv",
    mime="text/csv"
)

# System Limitations & Future Improvements
st.markdown("---")
st.header("⚠️ System Limitations & Future Improvements")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📐 Camera Calibration")
    st.markdown("""
    **Current State:**
    - Using approximate camera parameters
    - Assumed horizontal camera mounting
    
    **Improvements:**
    - Full camera intrinsic calibration
    - Extrinsic parameter estimation
    - Lens distortion correction
    - Dynamic horizon detection
    """)

with col2:
    st.subheader("🔄 Multi-frame Fusion")
    st.markdown("""
    **Current State:**
    - Each frame processed independently
    - Multiple detections of same sign
    
    **Improvements:**
    - Track objects across frames
    - Merge duplicate detections
    - Kalman filtering for positions
    - Confidence boosting via tracking
    """)

with col3:
    st.subheader("📍 Real-time GPS Integration")
    st.markdown("""
    **Current State:**
    - Using simulated GPS data
    - Fixed distance assumptions
    
    **Improvements:**
    - Real GPS/IMU integration
    - SLAM for accurate positioning
    - Vehicle odometry fusion
    - Accurate distance estimation
    """)

# Additional Notes
st.markdown("---")
st.info("""
**Note:** This dashboard demonstrates the traffic sign detection and mapping pipeline. 
For production use, real GPS/heading data and proper camera calibration are required for accurate results.
""")

# Footer
st.markdown("---")
st.caption("Traffic Sign Mapping Dashboard | Powered by YOLOv8, OpenStreetMap, and Streamlit")
