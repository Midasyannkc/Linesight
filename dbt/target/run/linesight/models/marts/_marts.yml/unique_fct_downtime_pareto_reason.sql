
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    reason as unique_field,
    count(*) as n_records

from "linesight"."main_marts"."fct_downtime_pareto"
where reason is not null
group by reason
having count(*) > 1



  
  
      
    ) dbt_internal_test