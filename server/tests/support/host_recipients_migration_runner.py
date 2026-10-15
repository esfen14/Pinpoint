"""Rehearse the host-recipient migration on populated throwaway databases."""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.getcwd())
with tempfile.TemporaryDirectory() as tmp:
    system_path = os.path.join(tmp, 'system.db')
    history_path = os.path.join(tmp, 'history.db')
    os.environ['DATABASE_URL'] = 'sqlite:///' + system_path
    os.environ['SECRET_KEY'] = 'test-key'
    os.environ['PINPOINT_SCHEDULER'] = '0'
    import config
    config.Config.SQLALCHEMY_BINDS = {'history': 'sqlite:///' + history_path}
    import flask_migrate
    from app import app
    before, target = 'c5e2a8f4d716', 'a79e14c0b621'
    report = {}

    def migrate(revision, down=False):
        with app.app_context():
            (flask_migrate.downgrade if down else flask_migrate.upgrade)(directory='migrations', revision=revision)

    def populate(conn, table, overrides):
        """Fill required legacy fields while preserving explicit fixture values."""
        values = dict(overrides)
        for _, name, kind, required, default, primary in conn.execute(f'PRAGMA table_info("{table}")'):
            if name not in values and required and default is None:
                values[name] = '2026-01-01' if 'DATE' in kind else 'fixture' if 'CHAR' in kind else 1
        fields = ', '.join('"' + name + '"' for name in values)
        conn.execute(f'INSERT INTO "{table}" ({fields}) VALUES ({", ".join("?" for _ in values)})', list(values.values()))

    migrate(before)
    with sqlite3.connect(system_path) as conn:
        populate(conn, 'ROLE', {'RoleID': 1, 'Name': 'Administrator'})
        populate(conn, 'USER', {'UserID': 1, 'RoleID': 1, 'Email': 'existing@example.com', 'Status': 'ACTIVE'})
        populate(conn, 'ACTIVITY_LOG', {'LogID': 1, 'UserID': 1})
        populate(conn, 'NETWORK_DISCOVERY_STATUS', {'DiscoveryStatusID': 1, 'LogID': 1, 'Status': 'SUCCESS'})
        populate(conn, 'NETWORK_DISCOVERY', {'NetDiscoveryID': 1, 'DiscoveryStatusID': 1, 'IP_Address': '10.0.0.5', 'Network': '10.0.0.0/24', 'Nagios_Host_Name': 'legacy', 'Device_State': 'ACTIVE'})
    with sqlite3.connect(history_path) as conn:
        history_tables = list(conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name != 'alembic_version' ORDER BY name"))
    migrate(target)
    with sqlite3.connect(system_path) as conn:
        conn.execute('PRAGMA foreign_keys=ON')
        report['version'] = conn.execute('SELECT version_num FROM alembic_version').fetchall()
        report['empty'] = conn.execute('SELECT count(*) FROM HOST_ALERT_RECIPIENT').fetchone()[0]
        report['legacy'] = conn.execute('SELECT Nagios_Host_Name FROM NETWORK_DISCOVERY').fetchall()
        conn.execute('INSERT INTO HOST_ALERT_RECIPIENT VALUES (1,1)')
        conn.commit()
        errors = []
        for row in [(1, 1), (999, 1), (1, 999)]:
            try:
                conn.execute('INSERT INTO HOST_ALERT_RECIPIENT VALUES (?,?)', row)
            except sqlite3.IntegrityError:
                errors.append(row)
            conn.rollback()
        report['rejected'] = errors
        report['rows'] = conn.execute('SELECT * FROM HOST_ALERT_RECIPIENT').fetchall()
    with sqlite3.connect(history_path) as conn:
        report['history_unchanged'] = history_tables == list(conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name != 'alembic_version' ORDER BY name"))
    migrate(before, down=True)
    with sqlite3.connect(system_path) as conn:
        report['removed'] = conn.execute("SELECT name FROM sqlite_master WHERE name='HOST_ALERT_RECIPIENT'").fetchall() == []
        report['users'] = conn.execute('SELECT Email FROM USER').fetchall()
        report['devices'] = conn.execute('SELECT Nagios_Host_Name FROM NETWORK_DISCOVERY').fetchall()
    migrate(target)
    with sqlite3.connect(system_path) as conn:
        report['reupgrade_empty'] = conn.execute('SELECT count(*) FROM HOST_ALERT_RECIPIENT').fetchone()[0]
print('REPORT_BEGIN')
print(json.dumps(report))
print('REPORT_END')
