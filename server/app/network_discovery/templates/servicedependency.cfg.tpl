define servicedependency {{
    host_name                       {host_name}
    service_description             {master_service}
    dependent_host_name             {host_name}
    dependent_service_description   {dependent_service}
    execution_failure_criteria      n
    notification_failure_criteria   c,u
}}
