-- Test to ensure no detections have future recording timestamps
-- Indicates system clock issues or data corruption

select
    video_name,
    frame_number,
    recording_timestamp,
    current_timestamp() as current_time
from {{ ref('fct_map_audit') }}
where try_to_timestamp(recording_timestamp, 'DD/MM/YYYY HH24:MI:SS') > current_timestamp()
