-- Test to ensure at least 30% of high-confidence detections are verified
-- This prevents model drift or GPS calibration issues

with high_confidence_detections as (
    select
        count(*) as total_detections,
        sum(case when audit_status = 'VERIFIED' then 1 else 0 end) as verified_count
    from {{ ref('fct_map_audit') }}
    where confidence >= 0.7
)

select
    total_detections,
    verified_count,
    round(100.0 * verified_count / nullif(total_detections, 0), 2) as verification_rate_pct
from high_confidence_detections
where verification_rate_pct < 30  -- Fail if less than 30%
