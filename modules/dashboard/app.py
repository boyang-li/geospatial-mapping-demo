import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from config import get_snowflake_connection, get_config

# Page config
st.set_page_config(
    page_title="SentinelMap Dashboard",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1f77b4;}
    .metric-card {background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem;}
    .stMetric {text-align: center;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=30)
def load_summary_metrics():
    """Load aggregated metrics from fct_map_audit."""
    conn = get_snowflake_connection()
    query = """
    SELECT 
        COUNT(*) as total_detections,
        SUM(CASE WHEN AUDIT_STATUS = 'VERIFIED' THEN 1 ELSE 0 END) as verified_count,
        SUM(CASE WHEN AUDIT_STATUS = 'NEW_DISCOVERY' THEN 1 ELSE 0 END) as new_discovery_count,
        SUM(CASE WHEN AUDIT_STATUS = 'CLASS_MISMATCH' THEN 1 ELSE 0 END) as class_mismatch_count,
        (verified_count * 100.0 / NULLIF(total_detections, 0)) as avg_verification_rate
    FROM FCT_MAP_AUDIT
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df.iloc[0].to_dict()

@st.cache_data(ttl=30)
def load_detection_points(limit=50000):
    """Load detection points from fct_map_audit for heatmap."""
    conn = get_snowflake_connection()
    query = f"""
    SELECT 
        DETECTED_LAT as lat,
        DETECTED_LON as lon,
        DETECTED_CLASS as CLASS_NAME,
        AUDIT_STATUS as VERIFICATION_STATUS,
        CONFIDENCE
    FROM FCT_MAP_AUDIT
    WHERE DETECTED_LAT IS NOT NULL 
      AND DETECTED_LON IS NOT NULL
      AND DETECTED_LAT BETWEEN 43.5 AND 44.0
      AND DETECTED_LON BETWEEN -79.6 AND -79.0
    LIMIT {limit}
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=30)
def load_verification_trend():
    """Load daily verification rate trend."""
    conn = get_snowflake_connection()
    query = """
    SELECT 
        TRY_TO_DATE(RECORDING_TIMESTAMP, 'DD/MM/YYYY HH24:MI:SS') as DETECTION_DATE,
        COUNT(*) as TOTAL_DETECTIONS,
        (SUM(CASE WHEN AUDIT_STATUS = 'VERIFIED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as VERIFICATION_RATE
    FROM FCT_MAP_AUDIT
    WHERE TRY_TO_DATE(RECORDING_TIMESTAMP, 'DD/MM/YYYY HH24:MI:SS') IS NOT NULL
    GROUP BY DETECTION_DATE
    ORDER BY DETECTION_DATE DESC
    LIMIT 30
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=30)
def load_class_breakdown():
    """Load detection breakdown by class and status."""
    conn = get_snowflake_connection()
    query = """
    SELECT 
        DETECTED_CLASS as CLASS_NAME,
        AUDIT_STATUS as VERIFICATION_STATUS,
        COUNT(*) as count
    FROM FCT_MAP_AUDIT
    GROUP BY DETECTED_CLASS, AUDIT_STATUS
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def create_heatmap(df, config):
    """Create pydeck heatmap visualization."""
    # Ensure lowercase column names for pydeck
    df = df.copy()
    df.columns = df.columns.str.lower()
    
    layer = pdk.Layer(
        "HeatmapLayer",
        data=df,
        get_position=["lon", "lat"],
        aggregation=pdk.types.String("MEAN"),
        get_weight="confidence",
        radius_pixels=50,
        opacity=0.8,
    )
    
    view_state = pdk.ViewState(
        latitude=config['map_center_lat'],
        longitude=config['map_center_lon'],
        zoom=config['map_zoom'],
        pitch=0,
    )
    
    return pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{class_name}\nStatus: {verification_status}"}
    )

def create_scatterplot(df, config):
    """Create pydeck scatterplot colored by verification status."""
    # Ensure lowercase column names for pydeck
    df = df.copy()
    df.columns = df.columns.str.lower()
    
    # Color mapping
    color_map = {
        'VERIFIED': [0, 255, 0, 160],      # Green
        'NEW_DISCOVERY': [255, 165, 0, 160],  # Orange
        'CLASS_MISMATCH': [255, 0, 0, 160]    # Red
    }
    
    df['color'] = df['verification_status'].map(color_map)
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=15,
        pickable=True,
        opacity=0.6,
        filled=True,
    )
    
    view_state = pdk.ViewState(
        latitude=config['map_center_lat'],
        longitude=config['map_center_lon'],
        zoom=config['map_zoom'],
        pitch=0,
    )
    
    return pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
            "html": "<b>{class_name}</b><br/>Status: {verification_status}<br/>Confidence: {confidence:.2f}",
            "style": {"backgroundColor": "steelblue", "color": "white"}
        }
    )

def main():
    # Header
    st.markdown('<p class="main-header">🗺️ SentinelMap Dashboard</p>', unsafe_allow_html=True)
    st.markdown("**Real-time Traffic Sign Detection Analytics**")
    
    # Sidebar
    st.sidebar.header("⚙️ Settings")
    map_type = st.sidebar.selectbox("Map Type", ["Heatmap", "Scatter Plot", "Both"])
    max_points = st.sidebar.slider("Max Points", 1000, 100000, 50000, 1000)
    auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=False)
    
    if auto_refresh:
        st.sidebar.info(f"Next refresh: {datetime.now() + timedelta(seconds=30):%H:%M:%S}")
    
    # Load config
    config = get_config()
    
    # Load data
    with st.spinner("Loading data from Snowflake..."):
        metrics = load_summary_metrics()
        detection_df = load_detection_points(limit=max_points)
        trend_df = load_verification_trend()
        class_df = load_class_breakdown()
    
    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Detections",
            value=f"{int(metrics['TOTAL_DETECTIONS']):,}"
        )
    
    with col2:
        st.metric(
            label="Verified",
            value=f"{int(metrics['VERIFIED_COUNT']):,}",
            delta=f"{metrics['AVG_VERIFICATION_RATE']:.1f}%"
        )
    
    with col3:
        st.metric(
            label="New Discoveries",
            value=f"{int(metrics['NEW_DISCOVERY_COUNT']):,}"
        )
    
    with col4:
        st.metric(
            label="Mismatches",
            value=f"{int(metrics['CLASS_MISMATCH_COUNT']):,}"
        )
    
    st.divider()
    
    # Map Section
    st.subheader("📍 Detection Map")
    st.caption(f"Showing {len(detection_df):,} detections")
    
    if map_type == "Heatmap":
        st.pydeck_chart(create_heatmap(detection_df, config))
    elif map_type == "Scatter Plot":
        st.pydeck_chart(create_scatterplot(detection_df, config))
    else:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("**Heatmap**")
            st.pydeck_chart(create_heatmap(detection_df, config))
        with col_right:
            st.markdown("**Scatter Plot (by Status)**")
            st.pydeck_chart(create_scatterplot(detection_df, config))
    
    st.divider()
    
    # Analytics Section
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📈 Verification Rate Trend")
        fig_trend = px.line(
            trend_df,
            x='DETECTION_DATE',
            y='VERIFICATION_RATE',
            title='30-Day Verification Rate',
            labels={'VERIFICATION_RATE': 'Verification Rate (%)', 'DETECTION_DATE': 'Date'}
        )
        fig_trend.update_traces(line_color='#1f77b4', line_width=3)
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col_chart2:
        st.subheader("📊 Detection Breakdown")
        fig_class = px.bar(
            class_df,
            x='CLASS_NAME',
            y='COUNT',
            color='VERIFICATION_STATUS',
            title='Detections by Class and Status',
            labels={'COUNT': 'Count', 'CLASS_NAME': 'Class'},
            color_discrete_map={
                'VERIFIED': '#00ff00',
                'NEW_DISCOVERY': '#ffa500',
                'CLASS_MISMATCH': '#ff0000'
            }
        )
        st.plotly_chart(fig_class, use_container_width=True)
    
    # Footer
    st.divider()
    st.caption(f"Last updated: {datetime.now():%Y-%m-%d %H:%M:%S} | Data source: Snowflake SENTINEL_MAP.MARTS")
    
    # Auto refresh
    if auto_refresh:
        import time
        time.sleep(config['refresh_interval'])
        st.rerun()

if __name__ == "__main__":
    main()
