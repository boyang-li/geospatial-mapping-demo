{{
    config(
        materialized='view',
        tags=['staging', 'perception']
    )
}}

with source_data as (
    select
        record_content,
        record_metadata,
        ingested_at
    from {{ source('raw', 'stg_detections') }}
    where record_content is not null
),

flattened as (
    select
        -- Extract JSON fields from VARIANT column
        record_content:video_name::string as video_name,
        record_content:frame_number::integer as frame_number,
        record_content:timestamp_sec::float as timestamp_ms,
        record_content:class_name::string as object_class,
        record_content:confidence::float as confidence,
        record_content:vehicle_lat::float as latitude,
        record_content:vehicle_lon::float as longitude,
        record_content:vehicle_id::string as vehicle_id,
        record_content:recording_timestamp::string as recording_timestamp,
        
        -- Create geography point for spatial operations
        st_makepoint(
            record_content:vehicle_lon::float,
            record_content:vehicle_lat::float
        ) as detection_location,
        
        -- Metadata
        ingested_at as snowflake_ingested_at,
        current_timestamp() as dbt_updated_at
        
    from source_data
)

select
    *,
    -- Data quality flag
    case
        when latitude is null or longitude is null then 'missing_coordinates'
        when confidence < 0.3 then 'low_confidence'
        when object_class is null then 'missing_class'
        else 'valid'
    end as data_quality_flag
from flattened
where latitude is not null
  and longitude is not null
