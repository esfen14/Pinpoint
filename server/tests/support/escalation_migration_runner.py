"""Exercise escalation constraints on populated disposable system/history binds."""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.getcwd())
with tempfile.TemporaryDirectory() as directory:
    system_path = directory + '/system.db'
    history_path = directory + '/history.db'
    os.environ.update(DATABASE_URL='sqlite:///' + system_path, SECRET_KEY='test-only', PINPOINT_SCHEDULER='0')
    import config
    config.Config.SQLALCHEMY_BINDS = {'history': 'sqlite:///' + history_path}
    import flask_migrate
    from app import app

    def migrate(revision, down=False):
        with app.app_context():
            (flask_migrate.downgrade if down else flask_migrate.upgrade)(directory='migrations', revision=revision)

    def populate(connection, table, values):
        values = dict(values)
        for _, name, kind, required, default, _ in connection.execute(f'PRAGMA table_info("{table}")'):
            if name not in values and required and default is None:
                values[name] = '2026-01-01' if 'DATE' in kind else 'fixture' if 'CHAR' in kind else 1
        fields = ', '.join('"' + key + '"' for key in values)
        placeholders = ', '.join('?' for _ in values)
        connection.execute(f'INSERT INTO "{table}" ({fields}) VALUES ({placeholders})', list(values.values()))

    def previous_rows():
        with sqlite3.connect(system_path) as connection:
            return {table: connection.execute(f'SELECT * FROM "{table}"').fetchall()
                    for table in ('NETWORK_DISCOVERY', 'USER', 'HOST_ALERT_RECIPIENT', 'DEVICE_INTERFACE')}

    def history_schema():
        with sqlite3.connect(history_path) as connection:
            return connection.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name != 'alembic_version' ORDER BY name").fetchall()

    migrate('e79b7d3c2641')
    with sqlite3.connect(system_path) as connection:
        populate(connection, 'ROLE', {'RoleID': 1, 'Name': 'Administrator'})
        populate(connection, 'USER', {'UserID': 1, 'RoleID': 1, 'Email': 'existing@example.com', 'Status': 'ACTIVE'})
        populate(connection, 'ACTIVITY_LOG', {'LogID': 1, 'UserID': 1})
        populate(connection, 'NETWORK_DISCOVERY_STATUS', {'DiscoveryStatusID': 1, 'LogID': 1, 'Status': 'SUCCESS'})
        populate(connection, 'NETWORK_DISCOVERY', {'NetDiscoveryID': 1, 'DiscoveryStatusID': 1,
                 'IP_Address': '10.77.0.2', 'Network': '10.77.0.0/28', 'Nagios_Host_Name': 'existing', 'Device_State': 'ACTIVE'})
        connection.execute('INSERT INTO HOST_ALERT_RECIPIENT VALUES (1, 1)')
    previous = previous_rows()
    original_history = history_schema()
    migrate('cd74e5f8a2d5')
    with sqlite3.connect(system_path) as connection:
        connection.execute('PRAGMA foreign_keys=ON')
        empty = connection.execute('SELECT count(*) FROM ESCALATION').fetchone()[0]
        connection.execute("INSERT INTO ESCALATION VALUES (1, 2, 5, 10, 'pinpoint_host_1', 1)")
        connection.commit()
        rows = connection.execute('SELECT * FROM ESCALATION').fetchall()
        rejected = []
        for values in [(2, 8, 5, 10, 'system_users', None), (2, 0, 5, 10, 'system_users', None),
                       (2, 2, 5, 1441, 'system_users', None), (2, 2, 5, 10, 'system_users', 99999)]:
            try:
                connection.execute('INSERT INTO ESCALATION VALUES (?, ?, ?, ?, ?, ?)', values)
            except sqlite3.IntegrityError:
                rejected.append(values)
            connection.rollback()
        versions = connection.execute('SELECT version_num FROM alembic_version').fetchall()
    with sqlite3.connect(history_path) as connection:
        history_versions = connection.execute('SELECT version_num FROM alembic_version').fetchall()
    migrate('e79b7d3c2641', down=True)
    with sqlite3.connect(system_path) as connection:
        removed = not connection.execute("SELECT 1 FROM sqlite_master WHERE name='ESCALATION'").fetchall()
    migrate('cd74e5f8a2d5')
    with sqlite3.connect(system_path) as connection:
        reupgrade_empty = connection.execute('SELECT count(*) FROM ESCALATION').fetchone()[0]
    report = dict(empty=empty, reupgrade_empty=reupgrade_empty, rows=rows,
                  invalid_rejected=rejected, removed=removed,
                  preserved=previous_rows() == previous,
                  history_unchanged=history_schema() == original_history,
                  both_binds_single_version=len(versions) == 1 and versions == history_versions)
print('REPORT_BEGIN')
print(json.dumps(report))
print('REPORT_END')
