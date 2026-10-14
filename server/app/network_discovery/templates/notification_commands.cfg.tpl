define command {{
    command_name    {host_command}
    command_line    {python} -I {script} host "type=$NOTIFICATIONTYPE$" "host=$HOSTNAME$" "address=$HOSTADDRESS$" "state=$HOSTSTATE$" "output=$HOSTOUTPUT$" "comment=$NOTIFICATIONCOMMENT$" "timet=$TIMET$" "to=$CONTACTEMAIL$"
}}

define command {{
    command_name    {service_command}
    command_line    {python} -I {script} service "type=$NOTIFICATIONTYPE$" "host=$HOSTNAME$" "address=$HOSTADDRESS$" "service=$SERVICEDESC$" "state=$SERVICESTATE$" "output=$SERVICEOUTPUT$" "comment=$NOTIFICATIONCOMMENT$" "timet=$TIMET$" "to=$CONTACTEMAIL$"
}}
