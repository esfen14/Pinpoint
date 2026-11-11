# Pinpoint "appliance-lite": Ubuntu 22.04 (the installer's OS) with Nagios Core
# 4.5.11 + plugins 2.4.12 built from source, Apache on :8081, and the Pinpoint
# backend under Gunicorn. No systemd: supervisord runs the processes and small
# shims stand in for `sudo`, `systemctl` and `nmap-sudo`.
#
# Build context is the repository root (see lab/compose.yaml).
#
# Kept in step with PinPoint-Installer setup/ (manifest pp-mon-baseline-1;
# audited against installer main 9bc7150, #316). Deliberate lab-only
# differences are listed in docs/manuals/Local_Lab.md ("Deliberate lab
# differences"): no systemd or `make install-daemoninit`, shims for sudo and
# systemctl, interval_length=10, lab credentials, no PHP or web client build.
FROM ubuntu:22.04

# Versions, URLs and SHA-256 as in the installer's baseline manifest.
ARG NAGIOS_VERSION=4.5.11
ARG NAGIOS_SHA256=1bf85d6704a75e6b89a09844836f68b1cfc61ab1ef005574041e36e73fdb797a
ARG PLUGINS_VERSION=2.4.12
ARG PLUGINS_SHA256=9a246245d8270f15759763160c48df5dcdc2af9632733a5238930fde6778b578
ARG NCPA_SHA256=05ea975942fda38d1de6b224a339ce18959abe1bce73ac9c26fdee624f778cec
ARG PYTHON_VERSION=3.14
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential autoconf gettext openssl libssl-dev libgd-dev libmariadb-dev \
      libmariadb-dev-compat unzip wget curl ca-certificates python3 python3-pip \
      apache2 apache2-utils iputils-ping dnsutils snmp libnet-snmp-perl nmap \
      rsync supervisor procps openssh-client sqlite3 git \
    && rm -rf /var/lib/apt/lists/*

# ---- Nagios Core (same version, source and steps as the installer) ----
RUN cd /usr/local/src \
 && wget -q https://assets.nagios.com/downloads/nagioscore/releases/nagios-${NAGIOS_VERSION}.tar.gz \
 && echo "${NAGIOS_SHA256}  nagios-${NAGIOS_VERSION}.tar.gz" | sha256sum -c - \
 && tar xzf nagios-${NAGIOS_VERSION}.tar.gz && cd nagios-${NAGIOS_VERSION} \
 && ./configure --with-httpd-conf=/etc/apache2/sites-enabled >/dev/null \
 && make all >/dev/null \
 && make install-groups-users && usermod -a -G nagios www-data \
 && make install >/dev/null && make install-commandmode >/dev/null \
 && make install-config >/dev/null && make install-webconf >/dev/null

# Plugins with check_mysql, then check_ncpa.py with its interpreter line pointed
# at python3 (Ubuntu 22.04 has no "python"), as install-nagios-plugins.sh does.
RUN cd /usr/local/src \
 && wget -q https://nagios-plugins.org/download/nagios-plugins-${PLUGINS_VERSION}.tar.gz \
 && echo "${PLUGINS_SHA256}  nagios-plugins-${PLUGINS_VERSION}.tar.gz" | sha256sum -c - \
 && tar xzf nagios-plugins-${PLUGINS_VERSION}.tar.gz && cd nagios-plugins-${PLUGINS_VERSION} \
 && ./configure --with-nagios-user=nagios --with-nagios-group=nagios --with-mysql=/usr >/dev/null \
 && make >/dev/null && make install >/dev/null \
 && test -x /usr/local/nagios/libexec/check_mysql \
 && cd /usr/local/src \
 && wget -q https://assets.nagios.com/downloads/ncpa/check_ncpa.tar.gz \
 && echo "${NCPA_SHA256}  check_ncpa.tar.gz" | sha256sum -c - \
 && mkdir check_ncpa && tar xzf check_ncpa.tar.gz -C check_ncpa \
 && install -o nagios -g nagios -m 0755 "$(find check_ncpa -type f -name check_ncpa.py | head -n 1)" \
      /usr/local/nagios/libexec/check_ncpa.py \
 && sed -i -E '1s/^(#!.*[ \/]python)[[:space:]]*$/\13/' /usr/local/nagios/libexec/check_ncpa.py \
 && runuser -u nagios -- /usr/local/nagios/libexec/check_ncpa.py --help >/dev/null

# Nginx fronts Gunicorn on :80, like the installer (added after the slow Nagios
# layers so it does not invalidate their cache). libcap2-bin gives setcap; msmtp-mta
# and bsd-mailx give the /bin/mail that Nagios notification commands pipe to.
RUN apt-get update && apt-get install -y --no-install-recommends nginx libcap2-bin sudo msmtp-mta bsd-mailx \
 && rm -rf /var/lib/apt/lists/* /etc/nginx/sites-enabled/default
COPY lab/appliance/nginx-pinpoint.conf /etc/nginx/conf.d/pinpoint.conf

# ---- Python (uv, like the installer) and the backend's dependencies ----
ENV UV_PYTHON_INSTALL_DIR=/opt/pinpoint/python
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin INSTALLER_NO_MODIFY_PATH=1 sh \
 && uv python install ${PYTHON_VERSION} \
 && uv venv --python ${PYTHON_VERSION} /opt/pinpoint/venv
COPY server/requirements.txt /tmp/requirements.txt
RUN uv pip install --python /opt/pinpoint/venv/bin/python -r /tmp/requirements.txt "gunicorn>=25.1" \
 && uv pip check --python /opt/pinpoint/venv/bin/python

# ---- Apache on :8081, Nagios accounts and config, the pinpoint user ----
RUN useradd --system --user-group --home-dir /opt/pinpoint --no-create-home --shell /usr/sbin/nologin pinpoint \
 && usermod -aG nagios pinpoint \
 && a2enmod cgi >/dev/null \
 && echo "Listen 127.0.0.1:8081" > /etc/apache2/ports.conf \
 && a2dissite 000-default >/dev/null 2>&1 || true \
 && echo "ServerName localhost" > /etc/apache2/conf-available/servername.conf && a2enconf servername >/dev/null \
 && htpasswd -bc /usr/local/nagios/etc/htpasswd.users nagiosadmin lab-admin-pass \
 && htpasswd -b  /usr/local/nagios/etc/htpasswd.users pinpoint-api lab-api-pass \
 && chown root:www-data /usr/local/nagios/etc/htpasswd.users && chmod 640 /usr/local/nagios/etc/htpasswd.users \
 && for key in authorized_for_system_information authorized_for_configuration_information \
               authorized_for_all_hosts authorized_for_all_services; do \
      sed -i "s/^${key}=.*/&,pinpoint-api/" /usr/local/nagios/etc/cgi.cfg; \
    done \
 && for f in hosts plugin-services; do \
      echo "# Managed by the Pinpoint web interface." > /usr/local/nagios/etc/objects/$f.cfg \
      && chown pinpoint:nagios /usr/local/nagios/etc/objects/$f.cfg && chmod 664 /usr/local/nagios/etc/objects/$f.cfg \
      && printf '\n# Pinpoint: %s.cfg is generated by the web interface.\ncfg_file=/usr/local/nagios/etc/objects/%s.cfg\n' $f $f >> /usr/local/nagios/etc/nagios.cfg; \
    done \
 && chown -R nagios:nagios /usr/local/nagios/var \
 && install -d -m 755 -o root -g root /usr/local/nagios/var/spool \
 && install -d -m 2770 -o nagios -g pinpoint /usr/local/nagios/var/spool/pinpoint-events \
 && : > /etc/msmtprc && chown root:nagios /etc/msmtprc && chmod 640 /etc/msmtprc

# Real sudo with the installer's sudoers rules and root helpers (copied from
# PinPoint-Installer setup/, see lab/appliance/helpers/). Only `systemctl` is a
# shim, at the path the sudoers rules name (/usr/bin/systemctl).
COPY lab/appliance/shims/systemctl /usr/bin/systemctl
COPY lab/appliance/shims/nmap-sudo /usr/local/bin/nmap-sudo
COPY lab/appliance/helpers/pinpoint-apply-smtp lab/appliance/helpers/pinpoint-apply-resources /usr/local/sbin/
COPY lab/appliance/pp-sync lab/appliance/entrypoint.sh /usr/local/bin/
COPY lab/appliance/supervisord.conf /etc/supervisor/supervisord.conf
COPY lab/appliance/pinpoint.env /opt/lab/pinpoint.env
RUN chmod 755 /usr/bin/systemctl /usr/local/bin/nmap-sudo /usr/local/bin/pp-sync /usr/local/bin/entrypoint.sh \
 && chown root:root /usr/local/sbin/pinpoint-apply-smtp /usr/local/sbin/pinpoint-apply-resources \
 && chmod 755 /usr/local/sbin/pinpoint-apply-smtp /usr/local/sbin/pinpoint-apply-resources \
 && chown nagios:nagios /usr/local/nagios/etc/resource.cfg && chmod 660 /usr/local/nagios/etc/resource.cfg \
 && printf '%s\n' 'pinpoint ALL=(root) NOPASSWD: /usr/bin/systemctl reload nagios, /bin/systemctl reload nagios' > /etc/sudoers.d/pinpoint-nagios-reload \
 && printf '%s\n' 'pinpoint ALL=(root) NOPASSWD: /usr/bin/systemctl restart nagios' > /etc/sudoers.d/pinpoint-restart \
 && printf '%s\n' 'pinpoint ALL=(root) NOPASSWD: /usr/local/sbin/pinpoint-apply-smtp ""' > /etc/sudoers.d/pinpoint-apply-smtp \
 && printf '%s\n' 'pinpoint ALL=(root) NOPASSWD: /usr/local/sbin/pinpoint-apply-resources ""' > /etc/sudoers.d/pinpoint-apply-resources \
 && chmod 440 /etc/sudoers.d/pinpoint-* && visudo -cf /etc/sudoers.d/pinpoint-nagios-reload \
 && visudo -c >/dev/null \
 && dpkg-statoverride --update --add root pinpoint 0750 /usr/bin/nmap \
 && setcap cap_net_raw,cap_net_admin,cap_net_bind_service=eip /usr/bin/nmap \
 && mkdir -p /opt/pinpoint/Network-Diagnosis-System/server && chown -R pinpoint:pinpoint /opt/pinpoint/Network-Diagnosis-System

EXPOSE 80
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
