"""Static guards that keep lab/appliance aligned with the installer (#316).

The installer lives in a separate repository, so these tests pin the settings
the lab must copy from it. Update both sides together when the installer
changes; deliberate lab-only differences are listed in docs/manuals/Local_Lab.md.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APPLIANCE = ROOT / "lab" / "appliance"


def _read(name):
    return (APPLIANCE / name).read_text()


def test_sources_are_downloaded_from_installer_urls_and_verified():
    dockerfile = _read("Dockerfile")
    assert "assets.nagios.com/downloads/nagioscore/releases" in dockerfile
    assert "nagios-plugins.org/download" in dockerfile
    assert "sha256sum -c" in dockerfile
    assert "1bf85d6704a75e6b89a09844836f68b1cfc61ab1ef005574041e36e73fdb797a" in dockerfile
    assert "9a246245d8270f15759763160c48df5dcdc2af9632733a5238930fde6778b578" in dockerfile


def test_plugins_include_check_mysql_and_check_ncpa():
    dockerfile = _read("Dockerfile")
    assert "libmariadb-dev" in dockerfile
    assert "--with-mysql=/usr" in dockerfile
    assert "check_ncpa.py" in dockerfile
    assert "05ea975942fda38d1de6b224a339ce18959abe1bce73ac9c26fdee624f778cec" in dockerfile
    assert "python3" in dockerfile


def test_api_account_gets_only_the_installers_read_only_cgi_rights():
    dockerfile = _read("Dockerfile")
    assert "authorized_for_[a-z_]+" not in dockerfile
    for key in (
        "authorized_for_system_information",
        "authorized_for_configuration_information",
        "authorized_for_all_hosts",
        "authorized_for_all_services",
    ):
        assert key in dockerfile
    assert "root:www-data /usr/local/nagios/etc/htpasswd.users" in dockerfile


def test_generated_config_files_and_event_spool_exist():
    dockerfile = _read("Dockerfile")
    assert "for f in hosts plugin-services" in dockerfile
    assert "/usr/local/nagios/var/spool/pinpoint-events" in dockerfile
    assert "2770" in dockerfile
    assert "pinpoint-event-handler" in _read("entrypoint.sh")


def test_mail_transport_and_nmap_restriction_match_installer():
    dockerfile = _read("Dockerfile")
    assert "msmtp-mta" in dockerfile and "bsd-mailx" in dockerfile
    assert "/etc/msmtprc" in dockerfile
    assert "cap_net_raw,cap_net_admin,cap_net_bind_service=eip" in dockerfile
    assert "--add root pinpoint 0750 /usr/bin/nmap" in dockerfile
    assert "/opt/pinpoint/python" in dockerfile


def test_gunicorn_and_nginx_match_installer():
    supervisord = _read("supervisord.conf")
    assert "--timeout 300" in supervisord
    assert "--no-control-socket" in supervisord
    nginx = _read("nginx-pinpoint.conf")
    assert "client_max_body_size 50M" in nginx
    assert "proxy_read_timeout 300s" in nginx
    assert "X-Real-IP" in nginx and "X-Forwarded-Proto" in nginx


def test_real_sudo_and_root_helpers_match_installer():
    dockerfile = _read("Dockerfile")
    assert not (APPLIANCE / "shims" / "sudo").exists()
    assert "apt-get install -y --no-install-recommends nginx libcap2-bin sudo" in dockerfile
    for helper in ("pinpoint-apply-smtp", "pinpoint-apply-resources"):
        assert (APPLIANCE / "helpers" / helper).is_file()
        assert f"/usr/local/sbin/{helper}" in dockerfile
        assert f"/etc/sudoers.d/{helper}" in dockerfile
    assert "pinpoint ALL=(root) NOPASSWD: /usr/bin/systemctl reload nagios" in dockerfile
    assert "pinpoint ALL=(root) NOPASSWD: /usr/bin/systemctl restart nagios" in dockerfile
    assert "visudo -cf" in dockerfile
    assert "/usr/bin/systemctl" in dockerfile
    assert "--privileged" in _read("shims/nmap-sudo")


def test_mail_sink_is_wired_into_the_lab_and_smoke_test():
    compose = (ROOT / "lab" / "compose.yaml").read_text()
    assert "mail01:" in compose and "lab/mail/Dockerfile" in compose
    assert "mail-ca:/lab-mail-ca:ro" in compose
    entrypoint = _read("entrypoint.sh")
    assert "update-ca-certificates" in entrypoint
    smoke = (ROOT / "lab" / "smoke.py").read_text()
    assert "--mail-sink-url" in smoke and "notification_mail_check" in smoke
    assert "--mail-sink-url" in (ROOT / "scripts" / "lab").read_text()
