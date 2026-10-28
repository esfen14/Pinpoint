FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d \
    && chmod 755 /usr/sbin/policy-rc.d \
    && apt-get update && apt-get install -y --no-install-recommends \
       python3 supervisor openssh-server openssh-client nginx openssl ca-certificates \
       dnsmasq-base isc-dhcp-client iproute2 iputils-ping iputils-arping procps \
       snmpd vsftpd postfix dovecot-imapd postgresql-16 postgresql-client-16 \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/ssh/ssh_host_* /etc/machine-id \
    && ln -s /identity/machine-id /etc/machine-id \
    && mkdir -p /identity /data /etc/pinpoint-defense /opt/pinpoint/defense /run/sshd \
    && chmod 700 /identity /data /etc/pinpoint-defense
COPY demo/defense /opt/pinpoint/defense
LABEL org.pinpoint.defense.issue="274"
CMD ["python3", "/opt/pinpoint/defense/node.py"]
