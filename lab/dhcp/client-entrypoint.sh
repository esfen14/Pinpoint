#!/bin/sh
# Keep each container's machine and SSH identity across docker restart.
set -eu
if [ ! -s /etc/machine-id ]; then
  tr -d '-' </proc/sys/kernel/random/uuid >/etc/machine-id
fi
ssh-keygen -A >/dev/null
printf 'send dhcp-client-identifier "pinpoint-dhcp187-%s";\n' "$1" >/etc/dhcp/dhclient-eth1.conf
hostname="$1"
printf 'server { listen 80; location / { return 200 "%s alive\\n"; add_header Content-Type text/plain; } }\n' "$hostname" >/etc/nginx/conf.d/dhcp-client.conf
rm -f /etc/nginx/sites-enabled/default
/usr/sbin/sshd
exec nginx -g 'daemon off;'
