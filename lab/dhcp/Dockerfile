FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 isc-dhcp-client dnsmasq-base iputils-ping curl procps \
    openssh-server openssh-client nginx ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /run/sshd \
    && rm -f /etc/ssh/ssh_host_* /etc/machine-id
COPY lab/dhcp/client-entrypoint.sh /usr/local/bin/dhcp-client-entrypoint
RUN chmod 755 /usr/local/bin/dhcp-client-entrypoint
CMD ["sleep", "infinity"]
