# SentinelMap Dashboard

Real-time visualization dashboard for traffic sign detection analytics.

## Features

- **Detection Heatmap**: Density visualization of traffic sign detections across Toronto area
- **Scatter Plot**: Color-coded by verification status (verified/new discovery/mismatch)
- **Summary Metrics**: Total detections, verification rate, new discoveries, mismatches
- **Verification Trend**: 30-day rolling verification rate
- **Class Breakdown**: Detections by class (traffic light, stop sign) and status
- **Auto-refresh**: Optional 30-second refresh interval

## Quick Start

### 1. Install Dependencies

```bash
cd modules/dashboard
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Snowflake credentials
```

### 3. Run Dashboard

```bash
streamlit run app.py
```

Dashboard will open at http://localhost:8501

## Configuration

Edit `.env` file:

```bash
# Snowflake Connection
SNOWFLAKE_ACCOUNT=SMAIKZB-IZC24119
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=SENTINEL_MAP
SNOWFLAKE_SCHEMA=MARTS
SNOWFLAKE_ROLE=SENTINEL_ROLE

# Dashboard Settings
REFRESH_INTERVAL_SECONDS=30
MAP_CENTER_LAT=43.790
MAP_CENTER_LON=-79.314
MAP_ZOOM=11
```

## Data Sources

Dashboard queries the following dbt marts:

- `AUDIT_SUMMARY_METRICS`: Aggregated daily metrics
- `FCT_MAP_AUDIT`: Individual detection records with OSM verification status
- `DISCREPANCY_DETAILS`: Mismatches requiring review

## Usage

### Map Controls

- **Map Type**: Switch between heatmap, scatter plot, or side-by-side view
- **Max Points**: Limit number of points loaded (1k-100k) for performance
- **Auto Refresh**: Enable 30-second automatic data refresh

### Metrics

- **Total Detections**: All detections in last 30 days
- **Verified**: Detections matched to OSM within 10m
- **New Discoveries**: Detections >10m from any OSM node (potential map updates)
- **Mismatches**: Detections within 10m but wrong class (data quality issues)

### Color Coding

- 🟢 **Green**: Verified (matched to OSM)
- 🟠 **Orange**: New Discovery (candidate for OSM contribution)
- 🔴 **Red**: Class Mismatch (requires review)

## Performance

- Default: 50k points (~2-3s load time)
- Max: 100k points (~5-7s load time)
- Caching: 30-second TTL on Snowflake queries

## Troubleshooting

**"Could not connect to Snowflake"**
- Verify credentials in `.env`
- Check warehouse is running (`ALTER WAREHOUSE COMPUTE_WH RESUME;`)
- Confirm role has SELECT permissions on MARTS schema

**"No data displayed"**
- Run dbt models first: `cd analytics && dbt run`
- Check `FCT_MAP_AUDIT` has records: `SELECT COUNT(*) FROM FCT_MAP_AUDIT;`

**Slow performance**
- Reduce `Max Points` slider
- Check Snowflake query history for long-running queries
- Consider adding spatial indexing on lat/lon columns
