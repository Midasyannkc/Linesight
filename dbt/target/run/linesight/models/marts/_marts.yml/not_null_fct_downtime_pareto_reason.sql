
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select reason
from "linesight"."main_marts"."fct_downtime_pareto"
where reason is null



  
  
      
    ) dbt_internal_test