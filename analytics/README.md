# SentinelMap Analytics (dbt Cloud)

This directory contains the dbt models for transforming raw perception data into actionable insights.

## Architecture

```
┌─────────────────┐
│  RAW Layer      │  STG_DETECTIONS (Kafka → Snowpipe)
│                 │  REF_OSM_NODES (OpenStreetMap ground truth)
└────────┬────────┘
         │
┌────────▼────────┐
│ STAGING Layer   │  stg_perception_data (flatten VARIANT JSON)
│                 │  stg_osm_ground_truth (normalize OSM types)
└────────┬────────┘
         │
┌────────▼────────┐
│  CORE Layer     │  fct_map_audit (spatial join with ST_DISTANCE)
│                 │  • VERIFIED: ≤10m match with correct type
│                 │  • CLASS_MISMATCH: ≤10m but wrong type
│                 │  • NEW_DISCOVERY: >10m or no OSM match
└────────┬────────┘
         │
┌────────▼────────┐
│  MARTS Layer    │  audit_summary_metrics (daily aggregations)
│                 │  discrepancy_details (review queue)
└─────────────────┘
```

## Quick Start

### 1. Prerequisites
- Snowflake account with SENTINEL_ROLE configured
- Python 3.9+ with virtual environment
- dbt Cloud account (for production) OR dbt Core (for local development)

### 2. Local Development Setup

```bash
# Create profiles.yml from example
cp profiles.yml.example profiles.yml
# Edit profiles.yml with your credentials

# Create .env file
echo "SNOWFLAKE_PASSWORD=your_password_here" > .env

# Install dependencies (if not already in venv)
pip install dbt-snowflake==1.8.3

# Install dbt packages
dbt deps

# Test connection
dbt debug

# Build all models
dbt run

# Run data quality tests
dbt test
```

### 3. dbt Cloud Setup

1. **Create dbt Cloud project** → Connect to GitHub → Select `sentinel-map` repo
2. **Set subdirectory**: `analytics` (Project Settings)
3. **Create Development environment**:
   - Connection: Snowflake credentials from Module C setup
   - Schema: `DBT_DEV`
   - Target: `dev`
4. **Create Production environment**:
   - Schema: `ANALYTICS`
   - Target: `prod`
5. **Create scheduled job**: Run `dbt build` daily after new data arrives

## Models

### Staging Layer
- **stg_perception_data**: Flattens VARIANT JSON from Kafka, creates GEOGRAPHY points, validates data quality
- **stg_osm_ground_truth**: Normalizes OSM types for matching (traffic_signals → traffic light)

### Core Layer
- **fct_map_audit**: Spatial join using ST_DISTANCE (≤100m pre-filter), classifies detections with 10m threshold

### Marts Layer
- **audit_summary_metrics**: Daily aggregations by class and status with verification rates
- **discrepancy_details**: Prioritized review queue (HIGH/MEDIUM/LOW) for CLASS_MISMATCH and NEW_DISCOVERY

## Custom Tests

- **assert_high_verification_rate**: Ensures ≥30% of high-confidence detections verified (prevents GPS drift)
- **assert_no_future_dates**: Detects system clock issues

## Configuration

Edit `dbt_project.yml` to adjust:
- `audit_threshold_meters`: Distance threshold for VERIFIED status (default: 10m)
- Materialization strategy per layer
- Schema naming conventions

## Data Quality

16 tests covering:
- Source data integrity (not_null, unique)
- Business logic (accepted_values, accepted_range)
- Spatial validity (distance ≥ 0)
- Temporal validity (no future dates)

## JSON Field Mapping

**Input JSON** (from Kafka):
```json
{
  "class_name": "traffic light",
  "vehicle_lat": 43.797135,
  "vehicle_lon": -79.315975,
  "recording_timestamp": "18/01/2026 19:15:36",
  "timestamp_sec": 24,
  ...
}
```

**dbt Model Mapping**:
- `class_name` → `object_class`
- `vehicle_lat` → `latitude`
- `vehicle_lon` → `longitude`
- `timestamp_sec` → `timestamp_ms`
- `recording_timestamp` → parsed with `TRY_TO_DATE('DD/MM/YYYY HH24:MI:SS')`

## Querying Results

```sql
USE ROLE SENTINEL_ROLE;
USE DATABASE SENTINEL_MAP;

-- Summary metrics
SELECT * FROM DBT_DEV_MARTS.AUDIT_SUMMARY_METRICS
ORDER BY audit_date DESC;

-- Discrepancies needing review
SELECT * FROM DBT_DEV_MARTS.DISCREPANCY_DETAILS
WHERE action_priority = 'HIGH'
LIMIT 10;

-- Core fact table with spatial matching
SELECT 
    video_name,
    detected_class,
    audit_status,
    distance_meters,
    confidence
FROM DBT_DEV_CORE.FCT_MAP_AUDIT
LIMIT 100;
```

## Troubleshooting

**"Database Error: Insufficient privileges"**
- Run grants: `snowflake_grants.sql` as ACCOUNTADMIN

**"Invalid identifier" errors**
- Check JSON field names match actual data structure
- Verify source tables exist: `SHOW TABLES IN SCHEMA RAW;`

**Empty mart tables**
- Verify source data: `SELECT COUNT(*) FROM RAW.STG_DETECTIONS;`
- Check date parsing: Invalid dates become NULL with TRY_TO_DATE

**Low verification rates**
- Ensure OSM data covers detection area
- Check GPS accuracy (expected: ±5-10m)
- Adjust `audit_threshold_meters` if needed
