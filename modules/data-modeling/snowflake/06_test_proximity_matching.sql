-- ============================================================================
-- SentinelMap: Test Spatial Proximity Matching
-- ============================================================================

USE ROLE SENTINEL_ROLE;
USE WAREHOUSE SENTINEL_WH;
USE DATABASE SENTINEL_MAP;
USE SCHEMA RAW;

-- ============================================================================
-- Step 1: Verify data loaded
-- ============================================================================

SELECT 'Detections loaded' AS check_type, COUNT(*) AS count
FROM STG_DETECTIONS;

SELECT 'OSM nodes loaded' AS check_type, COUNT(*) AS count
FROM REF_OSM_NODES;

-- ============================================================================
-- Step 2: Sample detection data (extract from VARIANT JSON)
-- ============================================================================

SELECT 
    RECORD_CONTENT:detection_id::STRING AS detection_id,
    RECORD_CONTENT:class_name::STRING AS class_name,
    RECORD_CONTENT:vehicle_lat::FLOAT AS vehicle_lat,
    RECORD_CONTENT:vehicle_lon::FLOAT AS vehicle_lon,
    RECORD_CONTENT:recording_timestamp::STRING AS recording_timestamp,
    RECORD_CONTENT:confidence::FLOAT AS confidence,
    INGESTED_AT
FROM STG_DETECTIONS
LIMIT 5;

-- ============================================================================
-- Step 3: Test proximity matching (50 meter threshold)
-- ============================================================================

WITH detections AS (
    SELECT 
        RECORD_CONTENT:detection_id::STRING AS detection_id,
        RECORD_CONTENT:class_name::STRING AS class_name,
        RECORD_CONTENT:vehicle_lat::FLOAT AS vehicle_lat,
        RECORD_CONTENT:vehicle_lon::FLOAT AS vehicle_lon,
        RECORD_CONTENT:recording_timestamp::STRING AS recording_timestamp,
        RECORD_CONTENT:confidence::FLOAT AS confidence,
        TO_GEOGRAPHY(ST_MAKEPOINT(
            RECORD_CONTENT:vehicle_lon::FLOAT, 
            RECORD_CONTENT:vehicle_lat::FLOAT
        )) AS vehicle_location
    FROM STG_DETECTIONS
    WHERE RECORD_CONTENT:vehicle_lat IS NOT NULL
      AND RECORD_CONTENT:vehicle_lon IS NOT NULL
),
osm_nodes AS (
    SELECT 
        OSM_ID,
        OSM_TYPE,
        LATITUDE,
        LONGITUDE,
        TO_GEOGRAPHY(ST_MAKEPOINT(LONGITUDE, LATITUDE)) AS osm_location,
        TAGS
    FROM REF_OSM_NODES
)
SELECT 
    d.detection_id,
    d.class_name AS detected_class,
    d.vehicle_lat,
    d.vehicle_lon,
    d.recording_timestamp,
    d.confidence,
    o.OSM_ID,
    o.OSM_TYPE AS osm_type,
    o.LATITUDE AS osm_lat,
    o.LONGITUDE AS osm_lon,
    ROUND(ST_DISTANCE(d.vehicle_location, o.osm_location), 2) AS distance_meters,
    o.TAGS
FROM detections d
JOIN osm_nodes o
    ON ST_DISTANCE(d.vehicle_location, o.osm_location) <= 50  -- 50 meter threshold
ORDER BY d.detection_id, distance_meters
LIMIT 20;

-- ============================================================================
-- Step 4: Count matches per detection
-- ============================================================================

WITH detections AS (
    SELECT 
        RECORD_CONTENT:detection_id::STRING AS detection_id,
        RECORD_CONTENT:class_name::STRING AS class_name,
        TO_GEOGRAPHY(ST_MAKEPOINT(
            RECORD_CONTENT:vehicle_lon::FLOAT, 
            RECORD_CONTENT:vehicle_lat::FLOAT
        )) AS vehicle_location
    FROM STG_DETECTIONS
    WHERE RECORD_CONTENT:vehicle_lat IS NOT NULL
      AND RECORD_CONTENT:vehicle_lon IS NOT NULL
),
osm_nodes AS (
    SELECT 
        OSM_ID,
        TO_GEOGRAPHY(ST_MAKEPOINT(LONGITUDE, LATITUDE)) AS osm_location
    FROM REF_OSM_NODES
)
SELECT 
    d.detection_id,
    d.class_name,
    COUNT(o.OSM_ID) AS num_nearby_osm_nodes
FROM detections d
LEFT JOIN osm_nodes o
    ON ST_DISTANCE(d.vehicle_location, o.osm_location) <= 50
GROUP BY d.detection_id, d.class_name
ORDER BY num_nearby_osm_nodes DESC;

-- ============================================================================
-- Step 5: Summary statistics
-- ============================================================================

WITH detections AS (
    SELECT 
        RECORD_CONTENT:detection_id::STRING AS detection_id,
        TO_GEOGRAPHY(ST_MAKEPOINT(
            RECORD_CONTENT:vehicle_lon::FLOAT, 
            RECORD_CONTENT:vehicle_lat::FLOAT
        )) AS vehicle_location
    FROM STG_DETECTIONS
    WHERE RECORD_CONTENT:vehicle_lat IS NOT NULL
      AND RECORD_CONTENT:vehicle_lon IS NOT NULL
),
osm_nodes AS (
    SELECT 
        TO_GEOGRAPHY(ST_MAKEPOINT(LONGITUDE, LATITUDE)) AS osm_location
    FROM REF_OSM_NODES
),
matches AS (
    SELECT 
        d.detection_id,
        COUNT(o.osm_location) AS match_count
    FROM detections d
    LEFT JOIN osm_nodes o
        ON ST_DISTANCE(d.vehicle_location, o.osm_location) <= 50
    GROUP BY d.detection_id
)
SELECT 
    COUNT(*) AS total_detections,
    SUM(CASE WHEN match_count > 0 THEN 1 ELSE 0 END) AS detections_with_matches,
    SUM(CASE WHEN match_count = 0 THEN 1 ELSE 0 END) AS detections_without_matches,
    ROUND(AVG(match_count), 2) AS avg_matches_per_detection,
    MAX(match_count) AS max_matches
FROM matches;
