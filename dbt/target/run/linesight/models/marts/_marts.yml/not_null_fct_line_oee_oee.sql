
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select oee
from "linesight"."main_marts"."fct_line_oee"
where oee is null



  
  
      
    ) dbt_internal_test