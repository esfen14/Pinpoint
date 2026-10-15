define command {{
    command_name    pinpoint_event_handler_service
    command_line    {python} -I {script} service '$SERVICESTATE$' '$SERVICESTATETYPE$' '$SERVICEATTEMPT$' '$HOSTNAME$' '$SERVICEDESC$' '$LASTSERVICESTATECHANGE$'
}}

define command {{
    command_name    pinpoint_event_handler_host
    command_line    {python} -I {script} host '$HOSTSTATE$' '$HOSTSTATETYPE$' '$HOSTATTEMPT$' '$HOSTNAME$' '$LASTHOSTSTATECHANGE$'
}}
