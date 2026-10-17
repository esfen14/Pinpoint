#!/usr/bin/env python3
"""Opt-in issue #198 comparison using installed Core in an isolated temp tree.

Run as a lab operator/root on an exclusively reserved appliance with Core 4.5.11
and Pinpoint's Python dependencies. Never reads/writes live Nagios config, logs,
commands or application databases. The temporary Core has notifications disabled,
checks only local fixture files, and is always terminated on exit. CGI subprocesses
serve loopback only. --serve enables the local browser fixture on port 19198;
there is no credential or production auth bypass outside this temporary app.
"""
import argparse
import csv
import io
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import secrets
import signal
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlsplit


def wait_until(check, seconds=30):
    """Wait a bounded interval for one live test condition."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = check()
        if value:
            return value
        time.sleep(0.25)
    raise RuntimeError('Live fixture condition did not converge.')


def run(root, serve, evidence_dir):
    """Run a separate Core, native CGIs and real Flask routes with temporary state."""
    nagios = '/usr/local/nagios/bin/nagios'
    version_output = subprocess.run([nagios, '--version'], capture_output=True, text=True, check=True).stdout
    version = re.search(r'Nagios Core (\S+)', version_output).group(1)
    if version != '4.5.11':
        raise RuntimeError('This probe requires the approved Core 4.5.11 contract.')
    cgi = Path('/usr/local/nagios/sbin')
    core_dir = root / 'core'
    core_dir.mkdir()
    user = pwd.getpwnam('nagios')
    os.chown(core_dir, user.pw_uid, user.pw_gid)
    (core_dir / 'archives').mkdir()
    os.chown(core_dir / 'archives', user.pw_uid, user.pw_gid)
    state = core_dir / 'state'
    state.write_text('0')
    check = core_dir / 'check.py'
    check.write_text('import pathlib,sys\ns=int(pathlib.Path(__file__).with_name("state").read_text())\nprint("Fixture service state",s)\nsys.exit(s)\n')
    objects = core_dir / 'objects.cfg'
    objects.write_text(f'''define timeperiod {{
 timeperiod_name always
 alias Always
 sunday 00:00-24:00
 monday 00:00-24:00
 tuesday 00:00-24:00
 wednesday 00:00-24:00
 thursday 00:00-24:00
 friday 00:00-24:00
 saturday 00:00-24:00
}}
define command {{
 command_name fixture_check
 command_line /usr/bin/python3 {check}
}}
define command {{
 command_name fixture_host
 command_line /usr/local/nagios/libexec/check_dummy 0
}}
define command {{
 command_name fixture_notify
 command_line /bin/true
}}
define contact {{
 contact_name fixture-contact
 alias Fixture contact with no delivery
 host_notification_period always
 service_notification_period always
 host_notification_options n
 service_notification_options n
 host_notification_commands fixture_notify
 service_notification_commands fixture_notify
}}
define host {{
 contacts fixture-contact
 host_name fixture-host
 alias Fixture host
 address 127.0.0.1
 check_command fixture_host
 check_period always
 max_check_attempts 1
 check_interval 2
 retry_interval 1
 notification_interval 0
 notification_period always
 notifications_enabled 0
}}
define service {{
 contacts fixture-contact
 host_name fixture-host
 service_description Recorded / service
 check_command fixture_check
 check_period always
 max_check_attempts 1
 check_interval 2
 retry_interval 1
 notification_interval 0
 notification_period always
 notifications_enabled 0
}}
''')
    config = core_dir / 'nagios.cfg'
    config.write_text(f'''log_file={core_dir}/nagios.log
cfg_file={objects}
object_cache_file={core_dir}/objects.cache
precached_object_file={core_dir}/objects.precache
status_file={core_dir}/status.dat
status_update_interval=1
nagios_user=nagios
nagios_group=nagios
lock_file={core_dir}/nagios.pid
temp_file={core_dir}/nagios.tmp
log_archive_path={core_dir}/archives
command_file={core_dir}/nagios.cmd
check_external_commands=0
interval_length=1
execute_service_checks=1
execute_host_checks=1
accept_passive_service_checks=0
accept_passive_host_checks=0
enable_notifications=0
enable_event_handlers=0
enable_flap_detection=0
retain_state_information=0
log_rotation_method=n
log_initial_states=1
log_current_states=1
log_service_retries=1
service_inter_check_delay_method=n
host_inter_check_delay_method=n
service_check_timeout=5
host_check_timeout=5
check_result_path={core_dir}
''')
    cgi_config = core_dir / 'cgi.cfg'
    cgi_config.write_text(f'main_config_file={config}\nuse_authentication=0\n')
    verify = subprocess.run([nagios, '-v', str(config)], capture_output=True, text=True)
    if verify.returncode:
        raise RuntimeError('Isolated Core config validation failed: '+verify.stdout[-2000:])
    calls = []

    def native(name, params):
        env = {**os.environ, 'NAGIOS_CGI_CONFIG': str(cgi_config),
               'REQUEST_METHOD': 'GET', 'QUERY_STRING': urlencode(params)}
        began = time.monotonic()
        response = subprocess.run([str(cgi / name)], env=env, capture_output=True, timeout=10, check=True).stdout
        body = response[response.index(b'{'):]
        calls.append({'cgi': name, 'query': params.get('query'), 'seconds': round(time.monotonic()-began, 6), 'bytes': len(body)})
        return json.loads(body)

    def native_avail(start, end):
        params = {'host': 'fixture-host', 'service': 'Recorded / service',
                  't1': start, 't2': end, 'timeperiod': 'custom', 'csvoutput': '',
                  'assumeinitialstates': 'no', 'assumestateretention': 'yes',
                  'assumestatesduringnotrunning': 'no', 'includesoftstates': 'no', 'backtrack': 4}
        env = {**os.environ, 'NAGIOS_CGI_CONFIG': str(cgi_config), 'REQUEST_METHOD': 'GET', 'QUERY_STRING': urlencode(params)}
        output = subprocess.run([str(cgi/'avail.cgi')], env=env, capture_output=True, timeout=10, check=True).stdout.decode()
        rows = list(csv.DictReader(io.StringIO(output[output.index('HOST_NAME,'):]), skipinitialspace=True))
        if not rows:
            raise RuntimeError('Native availability CSV has no fixture row.')
        return rows[0]

    def current_state():
        try:
            data = native('statusjson.cgi', {'query': 'servicelist', 'details': 'true', 'formatoptions': 'enumerate'})
            return data['data']['servicelist']['fixture-host']['Recorded / service']['status']
        except (KeyError, ValueError, subprocess.SubprocessError):
            return None

    output = (core_dir / 'process.log').open('w')
    process = subprocess.Popen([nagios, str(config)], stdout=output, stderr=output, start_new_session=True)
    http = None
    try:
        wait_until(lambda: current_state() == 'ok')
        before = int(time.time())
        time.sleep(2)
        state.write_text('2')
        wait_until(lambda: current_state() == 'critical')
        time.sleep(3)
        state.write_text('0')
        wait_until(lambda: current_state() == 'ok')
        time.sleep(2)
        after = int(time.time()) - 1
        logs = (core_dir / 'nagios.log').read_text()
        transitions = []
        for line in logs.splitlines():
            if 'SERVICE ALERT: fixture-host;Recorded / service;' in line:
                transitions.append({'timestamp': int(line.split(']')[0][1:]), 'state': line.split(';')[2]})
        critical = next(row['timestamp'] for row in transitions if row['state'] == 'CRITICAL')
        recovered = next(row['timestamp'] for row in transitions if row['state'] == 'OK' and row['timestamp'] > critical)
        if not 0 < recovered-critical < 30:
            raise RuntimeError('Fixture outage was not shorter than Pinpoint minimum polling interval.')

        class CGIHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urlsplit(self.path)
                params = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
                name = parsed.path.rsplit('/', 1)[-1]
                if name not in ('archivejson.cgi', 'statusjson.cgi'):
                    self.send_error(404); return
                try:
                    body = json.dumps(native(name, params)).encode()
                    self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(body)
                except Exception:
                    self.send_error(502)

            def log_message(self, *_args):
                pass

        http = ThreadingHTTPServer(('127.0.0.1', 0), CGIHandler)
        threading.Thread(target=http.serve_forever, daemon=True).start()
        base = f'http://127.0.0.1:{http.server_port}'
        os.environ['PINPOINT_SCHEDULER'] = '0'
        os.environ['SECRET_KEY'] = secrets.token_hex(32)
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from config import Config
        Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///'+str(root/'system.db')
        Config.SQLALCHEMY_BINDS = {'history': 'sqlite:///'+str(root/'history.db')}
        Config.HOST_CONFIG_DIR = root / 'generated'
        Config.BACKUP_DIR = root / 'backups'
        Config.TESTING = True
        from app import app, db
        from app.nagios.service_availability import ARCHIVE_OPTIONS, normalize_services, summarize
        from app.system_models import Permission, Role, RolePermission, User, UserStatus, SystemSettings
        from flask import send_from_directory
        from flask_login import login_user
        app.config.update(NAGIOS_ARCHIVE_URL=base+'/archivejson.cgi', NAGIOS_STATUS_URL=base+'/statusjson.cgi',
                          NAGIOS_USERNAME='', NAGIOS_PASSWORD='')
        with app.app_context():
            db.create_all()
            permission = Permission(Name='system.report', Description='Fixture report access')
            role = Role(Name='Fixture report reader')
            user_row = User(Email='fixture@example.invalid', First_Name='Fixture', Last_Name='Reader',
                            Hashed_Password='unused-no-login-password', Role=role, Status=UserStatus.ACTIVE)
            db.session.add_all([role, user_row, RolePermission(Role=role, Permissions=permission), SystemSettings(Id=1)])
            db.session.commit()
            user_id = user_row.UserID

        @app.before_request
        def fixture_user():
            # Temporary loopback-only browser fixture, never production code.
            login_user(db.session.get(User, user_id))

        dist = Path(__file__).resolve().parents[3] / 'client/dist'

        @app.route('/')
        @app.route('/<path:path>')
        def fixture_frontend(path=''):
            return send_from_directory(dist, path if path and (dist/path).is_file() else 'index.html')

        from app.api.system import report as report_module
        actual_period = report_module.service_period
        # Fixed exact live outage window for reproducible native/API comparisons.
        def fixed_period():
            start, end, meta = actual_period()
            if meta['period'] == 'custom':
                meta.update(start=datetime.fromtimestamp(before, timezone.utc).isoformat(),
                            end=datetime.fromtimestamp(after, timezone.utc).isoformat(), start_ts=before, end_ts=after)
                return before, after, meta
            return start, end, meta
        report_module.service_period = fixed_period
        native_payload = native('archivejson.cgi', {**ARCHIVE_OPTIONS, 'starttime': before, 'endtime': after})
        expected = summarize(normalize_services(native_payload, before, after))
        native_csv = native_avail(before, after)
        assert int(native_csv['TOTAL_TIME_OK']) == expected['ok_seconds']
        assert int(native_csv['TOTAL_TIME_CRITICAL']) == expected['critical_seconds']
        assert round(float(native_csv['PERCENT_KNOWN_TIME_OK'].rstrip('%')), 2) == expected['uptime_pct']
        assert expected['critical_seconds'] == recovered-critical
        assert expected['known_seconds'] == after-before
        assert expected['unaccounted_seconds'] == 0
        results = []
        with app.test_client() as client:
            for view in ('network-services', 'device-services'):
                count = len(calls); began = time.monotonic()
                response = client.get('/api/system/report/'+view+'?period=custom&start=2024-01-01&end=2024-01-01')
                assert response.status_code == 200
                data = response.get_json()['data']
                for field in ('ok_seconds', 'critical_seconds', 'known_seconds', 'uptime_pct'):
                    assert data['summary'][field] == expected[field]
                used = calls[count:]
                assert len(used) == 2
                assert 'snapshot' not in json.dumps(data).lower()
                results.append({'view': view, 'case': 'live-recorded-outage', 'seconds': round(time.monotonic()-began, 6),
                                'response_bytes': len(response.data), 'calls': used, 'expected': expected})
                report_module.service_period = actual_period
                missing_response = client.get('/api/system/report/'+view+'?period=custom&start=2001-01-01&end=2001-01-01')
                assert missing_response.status_code == 200
                missing = missing_response.get_json()['data']['summary']
                assert missing['known_seconds'] == 0 and missing['uptime_pct'] is None
                assert missing['no_recorded_data_seconds'] == 86400
                missing_native = native_avail(978307200, 978393600)
                assert int(missing_native['TOTAL_TIME_OK']) == 0
                assert int(missing_native['TOTAL_TIME_UNDETERMINED']) == 86400
                results.append({'view': view, 'case': 'missing-history', 'known_seconds': 0,
                    'missing_seconds': 86400, 'native_avail_missing_seconds': 86400,
                    'native_no_data_seconds': missing['no_data_seconds'],
                    'engine_down_seconds': missing['nagios_not_running_seconds'],
                    'unaccounted_seconds': missing['unaccounted_seconds']})
                report_module.service_period = fixed_period
                for period in ('last_24h', 'last_90d'):
                    count = len(calls); began = time.monotonic()
                    response = client.get('/api/system/report/'+view+'?period='+period)
                    assert response.status_code == 200
                    summary = response.get_json()['data']['summary']
                    results.append({'view': view, 'case': period, 'seconds': round(time.monotonic()-began, 6),
                        'response_bytes': len(response.data), 'calls': calls[count:], 'known_seconds': summary['known_seconds'],
                        'missing_seconds': summary['no_recorded_data_seconds']})
        print(json.dumps({'core_version': version, 'window': [before, after], 'outage_seconds': recovered-critical,
                          'inventory': {'hosts': 1, 'services': 1},
                          'native_avail': {key: native_csv[key] for key in ('TOTAL_TIME_OK', 'TOTAL_TIME_CRITICAL', 'PERCENT_KNOWN_TIME_OK')}, 'results': results}), flush=True)
        if serve:
            # Keep fixture/browser inputs alive for at most five minutes.
            from werkzeug.serving import make_server
            server = make_server('127.0.0.1', 19198, app, threaded=True)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            print('BROWSER_FIXTURE_READY port=19198', flush=True)
            time.sleep(300)
            server.shutdown()
    finally:
        if http:
            http.shutdown()
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        process.wait(timeout=15)
        output.close()
        if evidence_dir:
            evidence_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
            shutil.copytree(core_dir, evidence_dir / 'core')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--evidence-dir', type=Path, help='New private directory for synthetic Core logs/config/status after cleanup; must not exist.')
    args = parser.parse_args()
    if args.evidence_dir and args.evidence_dir.exists():
        parser.error('Evidence directory must not already exist.')
    with tempfile.TemporaryDirectory(prefix='issue198-live-') as folder:
        os.chmod(folder, 0o755)
        run(Path(folder), args.serve, args.evidence_dir)
