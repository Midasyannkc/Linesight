-- CERTIFIED. OEE = availability x performance x quality. Performance
-- assumed 1.0 (no throughput-target data in this dataset); a real
-- deployment joins a target-rate table for the performance component.

{{ config(materialized='table') }}

select
    line_id,
    production_date,
    round(avg(availability), 4) as availability,
    round(avg(quality_rate), 4) as quality_rate,
    1.0 as performance_assumed,
    round(avg(availability) * avg(quality_rate) * 1.0, 4) as oee
from {{ ref('stg_machine_daily_oee') }}
group by line_id, production_date
