-- Staging over the table synced from Databricks (Delta Sharing or a
-- scheduled load, see snowflake_sync/schema.sql). This is the exact
-- bridge point between the two platforms in this hybrid architecture.

with source as (
    select * from "linesight"."raw"."fct_machine_daily_oee"
),

renamed as (
    select
        machine_id,
        line_id,
        cast(production_date as date) as production_date,
        cast(units_measured as integer) as units_measured,
        cast(units_in_spec as integer) as units_in_spec,
        cast(quality_rate as double) as quality_rate,
        cast(downtime_hours as double) as downtime_hours,
        cast(planned_hours as double) as planned_hours,
        cast(availability as double) as availability
    from source
)

select * from renamed