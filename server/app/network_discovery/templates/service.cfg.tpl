define service {{
    host_name                   {host_name}
    service_description         {service_name}
    check_command               {command} 
    max_check_attempts          {max_check_attempts}
    check_interval              {check_interval}
    retry_interval              {retry_interval}
    check_period                24x7{notification_fields}
    contact_groups               {contact_groups}
}}