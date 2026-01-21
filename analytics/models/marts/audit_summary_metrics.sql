{{
    config(
        materialized='table',
        tags=['marts', 'reporting']
    )
}}

select
    try_to_date(recording_timestamp, 'DD/MM/YYYY HH24:MI:SS') as audit_date,
    detected_class,
    audit_status,
    
    count(*) as detection_count,
    avg(confidence) as avg_confidence,
    avg(distance_meters) as avg_distance_meters,
    min(distance_meters) as min_distance_meters,
    max(distance_meters) as max_distance_meters,
    
    -- Calculate verification rate
    round(
        100.0 * sum(case when audit_status = 'VERIFIED' then 1 else 0 end) / count(*),
        2
    ) as verification_rate_pct,
    
    current_timestamp() as dbt_updated_at
    
from {{ ref('fct_map_audit') }}
group by 1, 2, 3
order by audit_date desc, detected_class, audit_status
