FROM ubuntu:24.04 AS packages
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
    && mkdir -p /identity /data /etc/pinpoint-defense /opt/pinpoint/targets /run/sshd \
    && chmod 700 /identity /data /etc/pinpoint-defense

# The NCPA deploy target (ssh-alt02 only, #336): what PinPoint's deploy script expects
# to find on a Linux device, plus a local copy of Nagios's repository. The demo network
# has no route, so the Ubuntu apt sources are removed and the mirror is the only one.
FROM packages AS ncpa-packages
COPY demo/targets/fetch_mirror.py /tmp/fetch_mirror.py
RUN apt-get update && apt-get install -y --no-install-recommends sudo curl gpg gpgv \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash -G sudo labadmin \
    && . /etc/os-release \
    && python3 -I /tmp/fetch_mirror.py /opt/pinpoint-mirror "$VERSION_CODENAME" \
    && chmod -R a+rX /opt/pinpoint-mirror \
    && rm -f /tmp/fetch_mirror.py /etc/apt/sources.list /etc/apt/sources.list.d/ubuntu.sources

# Built with `--target ncpa-target`.
FROM ncpa-packages AS ncpa-target
COPY demo/targets /opt/pinpoint/targets
COPY --chmod=755 demo/targets/systemctl_shim.py /usr/bin/systemctl
LABEL org.pinpoint.defense.issue="274"
CMD ["python3", "/opt/pinpoint/targets/node.py"]

# The default image, used by the other thirteen devices. Keep this stage last.
FROM packages AS lab
COPY demo/targets /opt/pinpoint/targets
LABEL org.pinpoint.defense.issue="274"
CMD ["python3", "/opt/pinpoint/targets/node.py"]
