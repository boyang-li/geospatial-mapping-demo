# OSM Data Download Scripts

## Recommended: Auto-Download from Detections

```bash
python download_osm_from_detections.py
```

**Why**: Automatically queries Snowflake for detection bounding box and downloads only relevant OSM data.

**Features**:
- Connects to Snowflake to get detection GPS bounds
- Queries Overpass API for traffic infrastructure in that area
- Saves to `local-mvp/osm.xml`
- No manual configuration needed

---

## Legacy Scripts (For Reference)

### download_osm_data.py
- Generic Overpass API downloader
- Requires manual bounding box configuration
- **Use Case**: Custom geographic areas

### download_toronto_osm.py
- Downloads entire Toronto from Geofabrik
- Large file (entire city, ~500MB)
- **Use Case**: City-wide analysis

### download_toronto_tiled.py
- Splits Toronto into smaller tiles
- For very large areas that exceed Overpass API limits
- **Use Case**: Large-scale data collection

---

## Usage

**Preferred workflow**:
1. Process videos with Module A (Perception)
2. Ingest detections to Snowflake via Kafka
3. Run `download_osm_from_detections.py` to get matching OSM data
4. Run `ingest_osm_to_snowflake.py` to upload ground truth

Only use legacy scripts if the auto-download fails or you need custom areas.
