FROM pinpoint-dhcp187-appliance-base:latest
RUN sed -i 's|^PINPOINT_NETWORKS=.*|PINPOINT_NETWORKS=10.79.0.0/28|' /opt/lab/pinpoint.env
