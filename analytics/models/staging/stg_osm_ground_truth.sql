{{
    config(
        materialized='view',
        tags=['staging', 'reference']
    )
}}

select
    osm_id,
    latitude,
    longitude,
    
    -- Normalize object types for matching
    case
        when lower(osm_type) = 'traffic_signals' then 'traffic light'
        when lower(osm_type) = 'stop' then 'stop sign'
        when lower(osm_type) like '%crossing%' then 'pedestrian crossing'
        else lower(osm_type)
    end as normalized_type,
    
    osm_type as original_osm_type,
    
    -- Create geography point
    st_makepoint(longitude, latitude) as osm_location,
    
    -- Parse tags if available
    tags:name::string as location_name,
    tags:crossing::string as crossing_type,
    
    current_timestamp() as dbt_updated_at
    
from {{ source('raw', 'ref_osm_nodes') }}
where latitude is not null
  and longitude is not null
