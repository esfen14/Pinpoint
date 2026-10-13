define contact {{
    name                            {template_name}
    service_notification_period     {period}
    host_notification_period        {period}
    service_notification_options    {service_options}
    host_notification_options       {host_options} 
    service_notification_commands   notify-service-by-email
    host_notification_commands      notify-host-by-email 
}}