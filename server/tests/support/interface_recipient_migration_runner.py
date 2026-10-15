"""Upgrade from either deployed branch and preserve its populated data."""
import json
import os
import sqlite3
import sys
import tempfile

before = sys.argv[1]
assert before in {'b7d3f1a9c264', 'a79e14c0b621'}
sys.path.insert(0, os.getcwd())
with tempfile.TemporaryDirectory() as temporary:
    system_path = os.path.join(temporary, 'system.db')
    history_path = os.path.join(temporary, 'history.db')
    os.environ.update(DATABASE_URL='sqlite:///' + system_path,
                      SECRET_KEY='test-only', PINPOINT_SCHEDULER='0')
    import config
    config.Config.SQLALCHEMY_BINDS = {'history': 'sqlite:///' + history_path}
    import flask_migrate
    from app import app

    def migrate(revision, down=False):
        with app.app_context():
            operation = flask_migrate.downgrade if down else flask_migrate.upgrade
            operation(directory='migrations', revision=revision)

    def populate(connection, table, values):
        values = dict(values)
        for _, name, kind, required, default, _ in connection.execute(f'PRAGMA table_info("{table}")'):
            if name not in values and required and default is None:
                values[name] = '2026-01-01' if 'DATE' in kind else 'fixture' if 'CHAR' in kind else 1
        fields = ', '.join('"' + key + '"' for key in values)
        placeholders = ', '.join('?' for _ in values)
        connection.execute(f'INSERT INTO "{table}" ({fields}) VALUES ({placeholders})', list(values.values()))

    def feature_rows():
        with sqlite3.connect(system_path) as connection:
            names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            return {table: connection.execute(f'SELECT * FROM "{table}" ORDER BY 1').fetchall()
                    for table in ('DEVICE_INTERFACE', 'HOST_ALERT_RECIPIENT') if table in names}

    def history_schema():
        with sqlite3.connect(history_path) as connection:
            return connection.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name != 'alembic_version' ORDER BY name").fetchall()

    migrate(before)
    with sqlite3.connect(system_path) as connection:
        populate(connection, 'ROLE', {'RoleID': 1, 'Name': 'Administrator'})
        populate(connection, 'USER', {'UserID': 1, 'RoleID': 1, 'Email': 'existing@example.com', 'Status': 'ACTIVE'})
        populate(connection, 'ACTIVITY_LOG', {'LogID': 1, 'UserID': 1})
        populate(connection, 'NETWORK_DISCOVERY_STATUS', {'DiscoveryStatusID': 1, 'LogID': 1, 'Status': 'SUCCESS'})
        populate(connection, 'NETWORK_DISCOVERY', {'NetDiscoveryID': 1, 'DiscoveryStatusID': 1,
                 'IP_Address': '10.77.0.2', 'Network': '10.77.0.0/28', 'Nagios_Host_Name': 'existing', 'Device_State': 'ACTIVE'})
        if before == 'b7d3f1a9c264':
            populate(connection, 'DEVICE_INTERFACE', {'DeviceInterfaceID': 1, 'NetDiscoveryID': 1,
                     'If_Index': 7, 'Name': 'uplink', 'Monitored': 1, 'Present': 1})
        else:
            connection.execute('INSERT INTO HOST_ALERT_RECIPIENT VALUES (1, 1)')
    existing = feature_rows()
    original_history = history_schema()
    migrate('head')
    upgraded = feature_rows()
    with sqlite3.connect(system_path) as connection:
        versions = connection.execute('SELECT version_num FROM alembic_version').fetchall()
        foreign_key_errors = connection.execute('PRAGMA foreign_key_check').fetchall()
    with sqlite3.connect(history_path) as connection:
        history_versions = connection.execute('SELECT version_num FROM alembic_version').fetchall()
    migrate(before, down=True)
    downgraded = feature_rows()
    migrate('head')
    reupgraded = feature_rows()
    with sqlite3.connect(system_path) as connection:
        legacy = connection.execute('SELECT Nagios_Host_Name FROM NETWORK_DISCOVERY').fetchall()
    report = {
        'upgraded': upgraded,
        'existing': existing,
        'downgraded': downgraded,
        'preserved_upgrade': all(upgraded[name] == rows for name, rows in existing.items()),
        # Rolling back a merge revision leaves both installed parent schemas/data intact.
        'preserved_downgrade': downgraded == upgraded,
        'preserved_reupgrade': all(reupgraded[name] == rows for name, rows in existing.items()),
        'other_table_empty': all(rows == [] for name, rows in upgraded.items() if name not in existing),
        'both_binds_single_version': len(versions) == 1 and versions == history_versions,
        'foreign_key_errors': foreign_key_errors,
        'history_unchanged': history_schema() == original_history,
        'legacy': legacy,
    }
print('REPORT_BEGIN')
print(json.dumps(report))
print('REPORT_END')
