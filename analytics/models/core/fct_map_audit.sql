{{
    config(
        materialized='table',
        tags=['core', 'audit']
    )
}}

with perception_data as (
    select * from {{ ref('stg_perception_data') }}
    where data_quality_flag = 'valid'
),

osm_data as (
    select * from {{ ref('stg_osm_ground_truth') }}
),

-- Spatial join: find nearest OSM nodes within 100m
proximity_matches as (
    select
        p.video_name,
        p.frame_number,
        p.timestamp_ms,
        p.object_class as detected_class,
        p.confidence,
        p.latitude as detected_lat,
        p.longitude as detected_lon,
        p.vehicle_id,
        p.recording_timestamp,
        p.detection_location,
        
        o.node_id as nearest_osm_node_id,
        o.normalized_type as osm_class,
        o.latitude as osm_lat,
        o.longitude as osm_lon,
        o.osm_location,
        
        st_distance(p.detection_location, o.osm_location) as distance_meters,
        
        rank() over (
            partition by p.video_name, p.frame_number
            order by st_distance(p.detection_location, o.osm_location)
        ) as proximity_rank
        
    from perception_data p
    left join osm_data o
        on st_distance(p.detection_location, o.osm_location) <= 100
)

select
    video_name,
    frame_number,
    timestamp_ms,
    detected_class,
    confidence,
    detected_lat,
    detected_lon,
    vehicle_id,
    recording_timestamp,
    detection_location,
    
    nearest_osm_node_id,
    osm_class,
    osm_lat,
    osm_lon,
    distance_meters,
    
    -- Audit classification
    case
        when distance_meters is null then 'NEW_DISCOVERY'
        when distance_meters <= {{ var('audit_threshold_meters') }} 
             and lower(detected_class) = lower(osm_class) then 'VERIFIED'
        when distance_meters <= {{ var('audit_threshold_meters') }} 
             and lower(detected_class) != lower(osm_class) then 'CLASS_MISMATCH'
        when distance_meters > {{ var('audit_threshold_meters') }} then 'NEW_DISCOVERY'
        else 'UNKNOWN'
    end as audit_status,
    
    current_timestamp() as dbt_updated_at
    
from proximity_matches
where proximity_rank = 1  -- Keep only nearest match per detection
