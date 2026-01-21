# Module C: Data Modeling & Cloud Ingestion

This module bridges Kafka streams and Snowflake analytics, including OSM ground truth ingestion and spatial proximity matching.

---

## 📁 Directory Structure

```
modules/data-modeling/
├── snowflake/
│   ├── 01_initial_setup.sql          # ✅ Database, warehouse, resource monitor
│   ├── 02_create_tables.sql          # ✅ STG_DETECTIONS and REF_OSM_NODES
│   ├── 03_configure_kafka_user.sql   # ✅ Kafka connector authentication
│   ├── 04_create_views.sql           # ✅ Flattened views for dbt
│   ├── 05_validation.sql             # ✅ Health checks
│   └── 06_test_proximity_matching.sql # ✅ Spatial join testing
├── scripts/
│   ├── ingest_osm_to_snowflake.py   # Upload OSM XML to Snowflake
│   ├── download_osm_from_detections.py  # Auto-download OSM for detection area
│   └── README.md                     # Script documentation
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variable template
└── README.md                         # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Snowflake account (free trial: $400 credits)
- Confluent Cloud Kafka cluster (from Module B)
- Python 3.9+ with `snowflake-connector-python`

---

### Step 1: Snowflake Account Setup

#### 1.1 Create Free Trial

1. Go to [signup.snowflake.com](https://signup.snowflake.com)
2. Choose **Standard Edition**
3. Select **AWS** → **US East (N. Virginia)** (lowest cost)
4. Activate 30-day trial ($400 credits)

#### 1.2 Initial Configuration

Run SQL scripts in **Snowflake Worksheets** (in order):

```sql
-- In Snowflake UI: Worksheets → + → SQL Worksheet

-- 1. Create database, warehouse, resource monitor
@snowflake/01_initial_setup.sql

-- 2. Create tables (STG_DETECTIONS, REF_OSM_NODES)
@snowflake/02_create_tables.sql

-- 3. Create flattened views
@snowflake/04_create_views.sql

-- 4. Run validation
@snowflake/05_validation.sql
```

**What this does**:
- ✅ Creates `SENTINEL_MAP` database with `RAW` schema
- ✅ Creates `SENTINEL_WH` warehouse (XSMALL, auto-suspend 60s)
- ✅ Sets resource monitor: $50 credit quota with auto-suspend at 90%
- ✅ Creates ingestion tables with GEOGRAPHY type for spatial queries

---

### Step 2: Kafka-Snowflake Connector (Optional)

**Skip this if testing locally.** This connects your Kafka stream from Module B to Snowflake.

<details>
<summary>Click to expand Kafka connector setup</summary>

#### 2.1 Configure Snowflake User

```sql
-- Run in Snowflake:
@snowflake/03_configure_kafka_user.sql
```

#### 2.2 Create Confluent Connector

1. Log into Confluent Cloud
2. Navigate to **Connectors** → **Add Connector**
3. Search "Snowflake Sink"
4. Configure:
   - **Topics**: `sentinel_map_detections`
   - **Snowflake URL**: `<YOUR_ACCOUNT>.snowflakecomputing.com`
   - **Database**: `SENTINEL_MAP`
   - **Schema**: `RAW`
   - **Table**: `STG_DETECTIONS`
   - **Ingestion Method**: `SNOWPIPE_STREAMING`
   - **Error Tolerance**: `none` (fail fast, don't hide errors)

**Critical**: Set **Error Tolerance = none** to see connector errors immediately.

</details>

---

### Step 3: OSM Ground Truth Ingestion

#### 3.1 Install Dependencies

```bash
cd modules/data-modeling
pip install -r requirements.txt
```

#### 3.2 Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env with your Snowflake credentials
nano .env
```

**Required settings**:
```bash
SNOWFLAKE_ACCOUNT=abc12345.us-east-1  # Find in Snowflake UI
SNOWFLAKE_USER=YOUR_USERNAME
SNOWFLAKE_PASSWORD=YOUR_PASSWORD
```

#### 3.3 Download OSM Data

**Option 1: Auto-download from Snowflake detections (Recommended)**
```bash
cd modules/data-modeling/scripts
python download_osm_from_detections.py
```
This queries Snowflake for your detection GPS bounds and downloads only relevant OSM nodes.

**Option 2: Download Toronto traffic infrastructure**
```bash
# Download via Overpass API (traffic signals, stop signs, etc.)
curl "https://overpass-api.de/api/interpreter" \
  --data-urlencode "data=[out:xml][timeout:300];
  area[name=\"Toronto\"]->.a;
  (
    node[\"highway\"=\"traffic_signals\"](area.a);
    node[\"highway\"=\"stop\"](area.a);
    node[\"traffic_sign\"](area.a);
  );
  out body;" > ../../data/toronto_traffic.xml
```

#### 3.4 Run Ingestion

```bash
# Upload OSM XML to Snowflake
python scripts/ingest_osm_to_snowflake.py
```

**Expected output**:
```
📖 Parsing /path/to/local-mvp/osm.xml...
✅ Found 51556 traffic infrastructure nodes
🚀 Uploading to Snowflake...
✅ Inserted batch 1/513

📊 Upload Summary:
   Total nodes: 51556
   Unique types: 12

✨ OSM ingestion complete!
```

---

### Step 4: Test Spatial Proximity Matching

```sql
-- Run in Snowflake:
@snowflake/06_test_proximity_matching.sql
```

**What this does**:
1. Extracts detection GPS from VARIANT JSON
2. Converts to GEOGRAPHY points
3. Joins with OSM nodes within 50 meters
4. Shows matched detections with distance

**Expected results**:
```
Total Detections: 20
Detections with Matches: 11
Match Rate: 55%
Avg Matches per Detection: 0.85
```

---

## 🔑 Key Features

### Table Schemas

#### STG_DETECTIONS (Kafka Ingestion)
```sql
CREATE TABLE STG_DETECTIONS (
    RECORD_METADATA VARIANT,        -- Kafka metadata
    RECORD_CONTENT VARIANT,         -- Raw JSON from Module B
    INGESTED_AT TIMESTAMP_NTZ,
    KAFKA_TOPIC VARCHAR(255),
    KAFKA_PARTITION NUMBER(10,0),
    KAFKA_OFFSET NUMBER(38,0),
    KAFKA_TIMESTAMP TIMESTAMP_NTZ
);
```

**JSON Schema in RECORD_CONTENT**:
```json
{
  "detection_id": "uuid",
  "vehicle_lat": 43.7900,
  "vehicle_lon": -79.3140,
  "recording_timestamp": "18/01/2026 19:15:12",
  "class_name": "traffic light",
  "confidence": 0.85,
  "pixel_u": 1234.5,
  "pixel_v": 567.8
}
```

#### REF_OSM_NODES (Ground Truth)
```sql
CREATE TABLE REF_OSM_NODES (
    OSM_ID VARCHAR(50) PRIMARY KEY,
    OSM_TYPE VARCHAR(50),
    LATITUDE NUMBER(10, 7),
    LONGITUDE NUMBER(10, 7),
    TAGS VARIANT,
    UPLOADED_AT TIMESTAMP_NTZ,
    SOURCE_FILE VARCHAR(255)
);
```

**Spatial Queries**:
```sql
-- Convert lat/lon to GEOGRAPHY on-the-fly
SELECT 
    OSM_ID,
    ST_DISTANCE(
        TO_GEOGRAPHY(ST_MAKEPOINT(LONGITUDE, LATITUDE)),
        TO_GEOGRAPHY(ST_MAKEPOINT(-79.314, 43.790))
    ) AS distance_meters
FROM REF_OSM_NODES
WHERE distance_meters <= 50;
```

---

## 💰 Cost Management

Current configuration limits spend to **$50 of $400 free trial credits**:

- ✅ XSMALL warehouse (cheapest: $2/hour when running)
- ✅ 60-second auto-suspend (stops billing after 1 min idle)
- ✅ Resource monitor: Hard stop at 90% quota ($45)

**Monitor usage**:
```sql
-- Check resource monitor status
SHOW RESOURCE MONITORS;

-- View credit consumption
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE WAREHOUSE_NAME = 'SENTINEL_WH'
ORDER BY START_TIME DESC
LIMIT 10;
```

---

## 🛠️ Troubleshooting

### Issue: "File not found: osm.xml"

**Solution**:
```bash
# Check if file exists
ls -la local-mvp/osm*.xml

# Download OSM data for your detection area
cd modules/data-modeling/scripts
python download_osm_from_detections.py
```

---

### Issue: "Snowflake connection failed"

**Solution**:
1. Check `.env` settings
2. Verify account identifier: `<locator>.<region>` (no https://)
3. Test credentials in Snowflake UI first

---

### Issue: "Connector showing 0 errors but no data in Snowflake"

**Root causes**:
1. **Error Tolerance = "all"** (connector silently swallows errors)
   - Fix: Change to **"none"** in connector settings
2. **Buffer not flushed** (only 26 messages sent)
   - Fix: Pause/Resume connector or wait 60-120 seconds
3. **Topic name mismatch** (producer sends to different topic)
   - Fix: Verify connector reads from `sentinel_map_detections`

---

## 📊 Data Flow

```
Module A (Perception) → CSV → Module B (Kafka Producer)
                                        ↓
                               Confluent Cloud
                                        ↓
                          Snowpipe Streaming Connector
                                        ↓
                        Snowflake STG_DETECTIONS (VARIANT)
                                        ↓
local-mvp/osm.xml → Python Script → REF_OSM_NODES (GEOGRAPHY)
                                        ↓
                          Spatial Join (ST_DISTANCE)
                                        ↓
                            Audit Results (dbt)
```

---

## 🗺️ Next Steps

- [ ] Set up dbt Cloud for transformation layer
- [ ] Create data quality tests (confidence > 0.5, GPS in valid range)
- [ ] Build audit dashboard in Streamlit
- [ ] Implement H3/S2 spatial indexing for faster joins
- [ ] Add time-series analysis (detection trends over time)

---

## 📚 Related Documentation

- [Module A (Perception)](../perception/README.md)
- [Module B (Ingestion)](../ingestion/README.md)
- [Script Documentation](scripts/README.md)
- [Main Project README](../../README.md)
- [Production Specs](../../docs/prod-specs-en.md)
