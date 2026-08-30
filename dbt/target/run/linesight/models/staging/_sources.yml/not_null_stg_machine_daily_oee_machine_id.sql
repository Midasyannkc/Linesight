
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select machine_id
from "linesight"."main_staging"."stg_machine_daily_oee"
where machine_id is null



  
  
      
    ) dbt_internal_test