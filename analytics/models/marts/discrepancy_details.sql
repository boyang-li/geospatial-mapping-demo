{{
    config(
        materialized='table',
        tags=['marts', 'review']
    )
}}

select
    video_name,
    frame_number,
    recording_timestamp,
    detected_class,
    confidence,
    detected_lat,
    detected_lon,
    osm_class,
    osm_lat,
    osm_lon,
    distance_meters,
    audit_status,
    
    -- Priority for manual review
    case
        when audit_status = 'CLASS_MISMATCH' and distance_meters <= 5 then 'HIGH'
        when audit_status = 'NEW_DISCOVERY' and confidence >= 0.8 then 'MEDIUM'
        when audit_status = 'CLASS_MISMATCH' and distance_meters > 5 then 'LOW'
        else 'INFO'
    end as action_priority,
    
    current_timestamp() as dbt_updated_at
    
from {{ ref('fct_map_audit') }}
where audit_status in ('CLASS_MISMATCH', 'NEW_DISCOVERY')
order by
    case action_priority
        when 'HIGH' then 1
        when 'MEDIUM' then 2
        when 'LOW' then 3
        else 4
    end,
    confidence desc,
    distance_meters
