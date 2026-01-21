{{
    config(
        materialized='view',
        tags=['staging', 'reference']
    )
}}

select
    node_id,
    lat as latitude,
    lon as longitude,
    
    -- Normalize object types for matching
    case
        when lower(type) = 'traffic_signals' then 'traffic light'
        when lower(type) = 'stop' then 'stop sign'
        when lower(type) like '%crossing%' then 'pedestrian crossing'
        else lower(type)
    end as normalized_type,
    
    type as original_osm_type,
    
    -- Create geography point
    st_makepoint(lon, lat) as osm_location,
    
    -- Parse tags if available
    tags:name::string as location_name,
    tags:crossing::string as crossing_type,
    
    current_timestamp() as dbt_updated_at
    
from {{ source('raw', 'ref_osm_nodes') }}
where lat is not null
  and lon is not null
