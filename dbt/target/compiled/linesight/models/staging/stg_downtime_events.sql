with source as (
    select * from "linesight"."raw"."downtime_events"
),

renamed as (
    select
        machine_id,
        line_id,
        cast(downtime_start_ts as timestamp) as downtime_start_ts,
        cast(downtime_hours as double) as downtime_hours,
        reason
    from source
)

select * from renamed