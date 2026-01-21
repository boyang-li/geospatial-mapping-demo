#!/usr/bin/env python3
"""
Analyze why detections and OSM nodes aren't matching
"""
import snowflake.connector
import os
from dotenv import load_dotenv

load_dotenv()

conn = snowflake.connector.connect(
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    warehouse='SENTINEL_WH',
    database='SENTINEL_MAP',
    schema='RAW'
)

cur = conn.cursor()

print("="*80)
print("DETECTION vs OSM MISMATCH ANALYSIS")
print("="*80)

# 1. Check detection classes
print("\n1. DETECTION CLASSES (from Kafka)")
print("-"*80)
cur.execute("""
SELECT 
    DETECTION_DATA:class_name::STRING AS class_name,
    COUNT(*) as count
FROM STG_DETECTIONS
GROUP BY class_name
ORDER BY count DESC
""")
for row in cur:
    print(f"  {row[0]}: {row[1]} detections")

# 2. Check OSM node types
print("\n2. OSM NODE TYPES (51,556 nodes)")
print("-"*80)
cur.execute("""
SELECT 
    OSM_TYPE,
    COUNT(*) as count
FROM REF_OSM_NODES
GROUP BY OSM_TYPE
ORDER BY count DESC
LIMIT 20
""")
for row in cur:
    print(f"  {row[0]}: {row[1]} nodes")

# 3. Sample detection coordinates
print("\n3. SAMPLE DETECTION COORDINATES")
print("-"*80)
cur.execute("""
SELECT 
    DETECTION_DATA:class_name::STRING AS class_name,
    DETECTION_DATA:vehicle_lat::FLOAT AS lat,
    DETECTION_DATA:vehicle_lon::FLOAT AS lon
FROM STG_DETECTIONS
LIMIT 10
""")
for row in cur:
    print(f"  {row[0]}: ({row[1]:.6f}, {row[2]:.6f})")

# 4. OSM coordinates for traffic_signals
print("\n4. SAMPLE OSM COORDINATES (traffic_signals)")
print("-"*80)
cur.execute("""
SELECT 
    OSM_TYPE,
    LATITUDE,
    LONGITUDE
FROM REF_OSM_NODES
WHERE OSM_TYPE = 'traffic_signals'
LIMIT 5
""")
for row in cur:
    print(f"  {row[0]}: ({row[1]:.6f}, {row[2]:.6f})")

# 5. Check proximity - any matches within 100m?
print("\n5. PROXIMITY CHECK (within 100 meters)")
print("-"*80)
cur.execute("""
SELECT 
    d.DETECTION_DATA:class_name::STRING AS detection_class,
    d.DETECTION_DATA:vehicle_lat::FLOAT AS det_lat,
    d.DETECTION_DATA:vehicle_lon::FLOAT AS det_lon,
    osm.OSM_TYPE,
    osm.LATITUDE AS osm_lat,
    osm.LONGITUDE AS osm_lon,
    ST_DISTANCE(
        TO_GEOGRAPHY('POINT(' || d.DETECTION_DATA:vehicle_lon::FLOAT || ' ' || d.DETECTION_DATA:vehicle_lat::FLOAT || ')'),
        TO_GEOGRAPHY('POINT(' || osm.LONGITUDE || ' ' || osm.LATITUDE || ')')
    ) AS distance_meters
FROM STG_DETECTIONS d
CROSS JOIN REF_OSM_NODES osm
WHERE ST_DISTANCE(
    TO_GEOGRAPHY('POINT(' || d.DETECTION_DATA:vehicle_lon::FLOAT || ' ' || d.DETECTION_DATA:vehicle_lat::FLOAT || ')'),
    TO_GEOGRAPHY('POINT(' || osm.LONGITUDE || ' ' || osm.LATITUDE || ')')
) < 100
ORDER BY distance_meters
LIMIT 10
""")
matches = cur.fetchall()
if matches:
    print(f"  ✅ Found {len(matches)} matches:")
    for row in matches:
        print(f"    {row[0]} ({row[1]:.6f}, {row[2]:.6f}) ↔ {row[3]} ({row[4]:.6f}, {row[5]:.6f}) = {row[6]:.1f}m")
else:
    print("  ❌ NO MATCHES FOUND")

# 6. Find nearest OSM node to each detection
print("\n6. NEAREST OSM NODE TO EACH DETECTION (top 5)")
print("-"*80)
cur.execute("""
WITH nearest_osm AS (
    SELECT 
        d.DETECTION_DATA:detection_id::STRING AS detection_id,
        d.DETECTION_DATA:class_name::STRING AS detection_class,
        d.DETECTION_DATA:vehicle_lat::FLOAT AS det_lat,
        d.DETECTION_DATA:vehicle_lon::FLOAT AS det_lon,
        osm.OSM_TYPE,
        osm.LATITUDE AS osm_lat,
        osm.LONGITUDE AS osm_lon,
        ST_DISTANCE(
            TO_GEOGRAPHY('POINT(' || d.DETECTION_DATA:vehicle_lon::FLOAT || ' ' || d.DETECTION_DATA:vehicle_lat::FLOAT || ')'),
            TO_GEOGRAPHY('POINT(' || osm.LONGITUDE || ' ' || osm.LATITUDE || ')')
        ) AS distance_meters,
        ROW_NUMBER() OVER (PARTITION BY d.DETECTION_DATA:detection_id::STRING ORDER BY ST_DISTANCE(
            TO_GEOGRAPHY('POINT(' || d.DETECTION_DATA:vehicle_lon::FLOAT || ' ' || d.DETECTION_DATA:vehicle_lat::FLOAT || ')'),
            TO_GEOGRAPHY('POINT(' || osm.LONGITUDE || ' ' || osm.LATITUDE || ')')
        )) AS rn
    FROM STG_DETECTIONS d
    CROSS JOIN REF_OSM_NODES osm
)
SELECT 
    detection_class,
    det_lat,
    det_lon,
    OSM_TYPE,
    osm_lat,
    osm_lon,
    distance_meters
FROM nearest_osm
WHERE rn = 1
ORDER BY distance_meters
LIMIT 5
""")
for row in cur:
    print(f"  {row[0]} ({row[1]:.6f}, {row[2]:.6f}) → nearest: {row[3]} ({row[4]:.6f}, {row[5]:.6f}) = {row[6]:.1f}m")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)

cur.close()
conn.close()
