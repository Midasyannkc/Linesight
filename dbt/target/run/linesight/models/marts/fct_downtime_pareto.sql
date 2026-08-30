
    

    create  table
      "linesight"."main_marts"."fct_downtime_pareto__dbt_tmp"
  
    
    as (
      -- CERTIFIED. Downtime-reason Pareto, the actionable list a plant
-- manager works from to prioritize improvement projects.



with by_reason as (
    select
        reason,
        count(*) as event_count,
        round(sum(downtime_hours), 2) as total_downtime_hours
    from "linesight"."main_staging"."stg_downtime_events"
    group by reason
)

select
    reason,
    event_count,
    total_downtime_hours,
    round(total_downtime_hours * 1.0 / sum(total_downtime_hours) over (), 4) as pct_of_total_downtime
from by_reason
order by total_downtime_hours desc
    );
    
  