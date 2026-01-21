#!/usr/bin/env python3
"""
SentinelMap Live Dashboard
Real-time visualization of traffic light detections vs. OSM ground truth
Connects directly to Snowflake (no dbt required)
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import snowflake.connector
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / 'modules' / 'data-modeling' / '.env'
if not env_path.exists():
    # Fallback if running from different location
    env_path = Path(__file__).parent.parent / 'data-modeling' / '.env'

if env_path.exists():
    load_dotenv(env_path, override=True)
else:
    st.warning(f"⚠️ .env file not found at {env_path}")

# Page configuration
st.set_page_config(
    page_title="SentinelMap Dashboard",
    page_icon="🗺️",
    layout="wide"
)

# Title
st.title("🗺️ SentinelMap: Automated Map Auditing Dashboard")
st.markdown("**Real-time detection stream** from dashcam footage → Kafka → Snowflake")
st.markdown("---")

@st.cache_resource
def get_snowflake_connection():
    """Create Snowflake connection (cached)"""
    # Get credentials from environment
    user = os.getenv('SNOWFLAKE_USER')
    password = os.getenv('SNOWFLAKE_PASSWORD')
    account = os.getenv('SNOWFLAKE_ACCOUNT')
    
    # Debug: Show what we got (without password)
    if not user or not password or not account:
        st.error("❌ Missing Snowflake credentials in environment variables")
        st.info(f"SNOWFLAKE_USER: {'✅ Set' if user else '❌ Missing'}")
        st.info(f"SNOWFLAKE_PASSWORD: {'✅ Set' if password else '❌ Missing'}")
        st.info(f"SNOWFLAKE_ACCOUNT: {'✅ Set' if account else '❌ Missing'}")
        st.code("""
# Fix: Ensure modules/data-modeling/.env contains:
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account.region
        """)
        return None
    
    try:
        conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE', 'SENTINEL_WH'),
            database=os.getenv('SNOWFLAKE_DATABASE', 'SENTINEL_MAP'),
            schema=os.getenv('SNOWFLAKE_SCHEMA', 'RAW')
        )
        return conn
    except Exception as e:
        st.error(f"❌ Snowflake connection failed: {e}")
        st.info("💡 Check modules/data-modeling/.env configuration")
        return None

@st.cache_data(ttl=10)  # Refresh every 10 seconds
def load_detections(_conn):
    """Load latest detections from Snowflake"""
    if _conn is None:
        return pd.DataFrame()
    
    query = """
    SELECT 
        RECORD_CONTENT:detection_id::STRING AS detection_id,
        RECORD_CONTENT:class_name::STRING AS class_name,
        RECORD_CONTENT:vehicle_lat::FLOAT AS lat,
        RECORD_CONTENT:vehicle_lon::FLOAT AS lon,
        RECORD_CONTENT:recording_timestamp::STRING AS timestamp,
        RECORD_CONTENT:confidence::FLOAT AS confidence,
        INGESTED_AT
    FROM STG_DETECTIONS
    WHERE RECORD_CONTENT:vehicle_lat IS NOT NULL
      AND RECORD_CONTENT:vehicle_lon IS NOT NULL
    ORDER BY INGESTED_AT DESC
    LIMIT 1000
    """
    
    try:
        df = pd.read_sql(query, _conn)
        return df
    except Exception as e:
        st.error(f"Error loading detections: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)  # Refresh every 5 minutes (OSM data rarely changes)
def load_osm_nodes(_conn):
    """Load OSM ground truth from Snowflake"""
    if _conn is None:
        return pd.DataFrame()
    
    query = """
    SELECT 
        OSM_ID,
        OSM_TYPE,
        LATITUDE AS lat,
        LONGITUDE AS lon,
        TAGS
    FROM REF_OSM_NODES
    LIMIT 10000
    """
    
    try:
        df = pd.read_sql(query, _conn)
        return df
    except Exception as e:
        st.error(f"Error loading OSM data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=10)
def load_match_statistics(_conn):
    """Load proximity matching statistics"""
    if _conn is None:
        return pd.DataFrame()
    
    query = """
    WITH detections AS (
        SELECT 
            RECORD_CONTENT:detection_id::STRING AS detection_id,
            RECORD_CONTENT:class_name::STRING AS class_name,
            TO_GEOGRAPHY(ST_MAKEPOINT(
                RECORD_CONTENT:vehicle_lon::FLOAT, 
                RECORD_CONTENT:vehicle_lat::FLOAT
            )) AS location
        FROM STG_DETECTIONS
        WHERE RECORD_CONTENT:vehicle_lat IS NOT NULL
          AND RECORD_CONTENT:vehicle_lon IS NOT NULL
    ),
    osm_nodes AS (
        SELECT 
            TO_GEOGRAPHY(ST_MAKEPOINT(LONGITUDE, LATITUDE)) AS location
        FROM REF_OSM_NODES
    ),
    matches AS (
        SELECT 
            d.detection_id,
            d.class_name,
            COUNT(o.location) AS nearby_osm_count
        FROM detections d
        LEFT JOIN osm_nodes o
            ON ST_DISTANCE(d.location, o.location) <= 50
        GROUP BY d.detection_id, d.class_name
    )
    SELECT 
        COUNT(*) AS total_detections,
        SUM(CASE WHEN nearby_osm_count > 0 THEN 1 ELSE 0 END) AS matched,
        SUM(CASE WHEN nearby_osm_count = 0 THEN 1 ELSE 0 END) AS unmatched,
        ROUND(AVG(nearby_osm_count), 2) AS avg_nearby_osm
    FROM matches
    """
    
    try:
        df = pd.read_sql(query, _conn)
        return df.iloc[0] if not df.empty else None
    except Exception as e:
        st.error(f"Error loading statistics: {e}")
        return None

# Connect to Snowflake
conn = get_snowflake_connection()

if conn:
    # Load data
    with st.spinner("Loading data from Snowflake..."):
        detections_df = load_detections(conn)
        osm_df = load_osm_nodes(conn)
        stats = load_match_statistics(conn)
    
    # Sidebar - Statistics
    st.sidebar.header("📊 Live Statistics")
    
    if stats is not None:
        total = int(stats['total_detections'])
        matched = int(stats['matched'])
        unmatched = int(stats['unmatched'])
        match_rate = (matched / total * 100) if total > 0 else 0
        
        st.sidebar.metric("Total Detections", total)
        st.sidebar.metric("Matched to OSM", matched, 
                         delta=f"{match_rate:.1f}% match rate")
        st.sidebar.metric("New Discoveries", unmatched,
                         delta="Not in OSM",
                         delta_color="inverse")
        st.sidebar.metric("Avg OSM Nodes Nearby", f"{stats['avg_nearby_osm']:.2f}")
    
    st.sidebar.markdown("---")
    st.sidebar.header("🗺️ Map Legend")
    st.sidebar.markdown("🔴 **Red**: New detections from videos")
    st.sidebar.markdown("🟢 **Green**: OSM ground truth")
    st.sidebar.markdown("⭕ **Blue circle**: 50m proximity zone")
    
    st.sidebar.markdown("---")
    st.sidebar.header("🔄 Data Freshness")
    if not detections_df.empty:
        latest = pd.to_datetime(detections_df['INGESTED_AT'].max())
        st.sidebar.write(f"Latest detection: {latest.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Main content - Map
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("🗺️ Interactive Map: Detections vs. Ground Truth")
        
        if not detections_df.empty:
            # Calculate map center (average of detection coordinates)
            center_lat = detections_df['lat'].mean()
            center_lon = detections_df['lon'].mean()
            
            # Create map
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=13,
                tiles='OpenStreetMap'
            )
            
            # Add OSM nodes (green)
            if not osm_df.empty:
                for _, row in osm_df.iterrows():
                    folium.CircleMarker(
                        location=[row['lat'], row['lon']],
                        radius=4,
                        color='green',
                        fill=True,
                        fillColor='green',
                        fillOpacity=0.6,
                        popup=f"OSM: {row['OSM_TYPE']}"
                    ).add_to(m)
            
            # Add detections (red)
            for _, row in detections_df.iterrows():
                # Main detection marker
                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=6,
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.8,
                    popup=f"""
                    <b>Detection</b><br>
                    Class: {row['class_name']}<br>
                    Confidence: {row['confidence']:.2f}<br>
                    Time: {row['timestamp']}<br>
                    GPS: ({row['lat']:.6f}, {row['lon']:.6f})
                    """
                ).add_to(m)
                
                # 50m proximity circle (semi-transparent)
                folium.Circle(
                    location=[row['lat'], row['lon']],
                    radius=50,  # meters
                    color='blue',
                    fill=True,
                    fillOpacity=0.1,
                    weight=1
                ).add_to(m)
            
            # Display map
            st_folium(m, width=900, height=600)
        else:
            st.warning("⚠️ No detections found. Process videos and publish to Kafka first.")
            st.code("""
# Run batch processing:
cd modules/perception
python batch_process.py --video-dir ../../data/videos --limit 5

# Publish to Kafka:
cd modules/ingestion
./bin/producer -csv ../../data/detections/batch_detections.csv -vehicle demo
            """)
    
    with col2:
        st.subheader("📋 Recent Detections")
        
        if not detections_df.empty:
            # Show latest 10 detections
            recent = detections_df.head(10)[['class_name', 'confidence', 'timestamp', 'lat', 'lon']]
            recent['confidence'] = recent['confidence'].apply(lambda x: f"{x:.2f}")
            recent['lat'] = recent['lat'].apply(lambda x: f"{x:.5f}")
            recent['lon'] = recent['lon'].apply(lambda x: f"{x:.5f}")
            
            st.dataframe(recent, hide_index=True, height=600)
        else:
            st.info("No recent detections")
    
    # Bottom section - Data Tables
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📊 Detection Details", "🗺️ OSM Nodes", "🔍 Proximity Matches"])
    
    with tab1:
        st.subheader(f"All Detections ({len(detections_df)} total)")
        if not detections_df.empty:
            st.dataframe(detections_df, height=400)
        else:
            st.info("No detections available")
    
    with tab2:
        st.subheader(f"OSM Ground Truth ({len(osm_df)} nodes)")
        if not osm_df.empty:
            st.dataframe(osm_df.head(100), height=400)
        else:
            st.info("No OSM data loaded")
    
    with tab3:
        st.subheader("Proximity Matching Results")
        if conn:
            match_query = """
            WITH detections AS (
                SELECT 
                    RECORD_CONTENT:detection_id::STRING AS detection_id,
                    RECORD_CONTENT:class_name::STRING AS class_name,
                    RECORD_CONTENT:vehicle_lat::FLOAT AS det_lat,
                    RECORD_CONTENT:vehicle_lon::FLOAT AS det_lon,
                    TO_GEOGRAPHY(ST_MAKEPOINT(
                        RECORD_CONTENT:vehicle_lon::FLOAT, 
                        RECORD_CONTENT:vehicle_lat::FLOAT
                    )) AS location
                FROM STG_DETECTIONS
                WHERE RECORD_CONTENT:vehicle_lat IS NOT NULL
                LIMIT 100
            ),
            osm_nodes AS (
                SELECT 
                    OSM_ID,
                    OSM_TYPE,
                    LATITUDE AS osm_lat,
                    LONGITUDE AS osm_lon,
                    TO_GEOGRAPHY(ST_MAKEPOINT(LONGITUDE, LATITUDE)) AS location
                FROM REF_OSM_NODES
            )
            SELECT 
                d.detection_id,
                d.class_name,
                d.det_lat,
                d.det_lon,
                o.OSM_ID,
                o.OSM_TYPE,
                o.osm_lat,
                o.osm_lon,
                ROUND(ST_DISTANCE(d.location, o.location), 2) AS distance_meters
            FROM detections d
            JOIN osm_nodes o
                ON ST_DISTANCE(d.location, o.location) <= 50
            ORDER BY distance_meters
            LIMIT 50
            """
            
            try:
                matches_df = pd.read_sql(match_query, conn)
                if not matches_df.empty:
                    st.dataframe(matches_df, height=400)
                    st.success(f"✅ Found {len(matches_df)} proximity matches within 50 meters")
                else:
                    st.warning("⚠️ No matches found within 50 meters")
            except Exception as e:
                st.error(f"Error running proximity query: {e}")

else:
    st.error("❌ Cannot connect to Snowflake")
    st.markdown("""
    ### Troubleshooting:
    
    1. Ensure Snowflake tables exist:
       - Run `modules/data-modeling/snowflake/01_initial_setup.sql`
       - Run `modules/data-modeling/snowflake/02_create_tables.sql`
    
    2. Verify Snowflake warehouse is running
    
    3. Check credentials in the script
    """)
