"""Exercise the topology merge on populated private databases; never installed data."""
import json
import os
import sqlite3
import sys
import tempfile
sys.path.insert(0, os.getcwd())
with tempfile.TemporaryDirectory() as tmp:
    system_path, history_path = os.path.join(tmp, 'system.db'), os.path.join(tmp, 'history.db')
    os.environ.update(DATABASE_URL='sqlite:///' + system_path, SECRET_KEY='test-key', PINPOINT_SCHEDULER='0')
    import config
    config.Config.SQLALCHEMY_BINDS = {'history': 'sqlite:///' + history_path}
    import flask_migrate
    from app import app
    def migrate(revision, down=False):
        """Apply a revision on both disposable database binds."""
        with app.app_context():
            (flask_migrate.downgrade if down else flask_migrate.upgrade)(directory='migrations', revision=revision)
    def populate(conn, table, overrides):
        """Insert fixtures with required columns and real foreign-key identities."""
        values = dict(overrides)
        for _, name, kind, required, default, primary in conn.execute(f'PRAGMA table_info("{table}")'):
            if name not in values and required and default is None:
                values[name] = '2026-01-01' if 'DATE' in kind else 'fixture' if 'CHAR' in kind else 1
        fields = ', '.join('"' + name + '"' for name in values)
        conn.execute(f'INSERT INTO "{table}" ({fields}) VALUES ({", ".join("?" for _ in values)})', list(values.values()))
    starting_head = sys.argv[1]
    assert starting_head in ('b117d9a2c041', '99f584ed8151')
    migrate(starting_head)
    with sqlite3.connect(system_path) as conn:
        populate(conn, 'ROLE', {'RoleID':1, 'Name':'Administrator'})
        populate(conn, 'USER', {'UserID':1, 'RoleID':1, 'Email':'existing@example.com', 'Status':'ACTIVE'})
        populate(conn, 'ACTIVITY_LOG', {'LogID':1, 'UserID':1})
        populate(conn, 'NETWORK_DISCOVERY_STATUS', {'DiscoveryStatusID':1, 'LogID':1, 'Status':'SUCCESS'})
        for i in range(1,4):
            populate(conn, 'NETWORK_DISCOVERY', {'NetDiscoveryID':i, 'DiscoveryStatusID':1, 'IP_Address':f'10.77.0.{i+2}', 'Network':'10.77.0.0/28', 'Nagios_Host_Name':f'legacy-{i}', 'Device_State':'ACTIVE'})

    def snapshot():
        """Read existing feature/device rows for exact preservation comparisons."""
        with sqlite3.connect(system_path) as conn:
            names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            return {name: conn.execute(f'SELECT * FROM "{name}" ORDER BY 1,2').fetchall()
                    for name in ('DEVICE_PARENT', 'ESCALATION', 'REMEDIATION_ACTION', 'REMEDIATION_RUN', 'NETWORK_DISCOVERY') if name in names}

    def seed_features(conn):
        """Save representative escalation settings and remediation action/run rows."""
        conn.execute("INSERT INTO ESCALATION VALUES (1, 2, 5, 10, 'system_users', 1)")
        populate(conn, 'REMEDIATION_ACTION', {'Id': 1, 'Name': 'Existing action', 'Action_Type': 'RECORD_ONLY',
                 'Scope_Kind': 'HOST', 'Host_Pattern': '*', 'Parameters': '{}'})
        populate(conn, 'REMEDIATION_RUN', {'Id': 1, 'Action_Id': 1, 'Action_Name': 'Existing action',
                 'Event_Key': 'existing-event', 'Hostname': 'legacy-1', 'State': 'DOWN',
                 'State_Type': 'HARD', 'Outcome': 'SUCCEEDED'})

    with sqlite3.connect(system_path) as conn:
        if starting_head == 'b117d9a2c041':
            conn.executemany('INSERT INTO DEVICE_PARENT VALUES (?,?)', [(1,2),(1,3)])
        else:
            seed_features(conn)
    existing = snapshot()
    with sqlite3.connect(history_path) as conn:
        conn.execute('CREATE TABLE topology_test_marker (value TEXT)')
        conn.execute("INSERT INTO topology_test_marker VALUES ('preserved')")
    migrate('head')
    report = {'existing_preserved': all(snapshot()[name] == rows for name, rows in existing.items())}
    with sqlite3.connect(system_path) as conn:
        if starting_head == 'b117d9a2c041':
            seed_features(conn)
        else:
            conn.executemany('INSERT INTO DEVICE_PARENT VALUES (?,?)', [(1,2),(1,3)])
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()
        versions = conn.execute('SELECT version_num FROM alembic_version').fetchall()
    joined = snapshot()
    migrate(starting_head, down=True)
    assert snapshot() == joined
    migrate('head')
    report['roundtrip_preserved'] = snapshot() == joined
    report['parents'] = snapshot()['DEVICE_PARENT']
    with sqlite3.connect(history_path) as conn:
        report['single_head'] = len(versions) == 1 and versions == conn.execute('SELECT version_num FROM alembic_version').fetchall()
        report['history_preserved'] = conn.execute('SELECT value FROM topology_test_marker').fetchone()[0] == 'preserved'
print('REPORT_BEGIN'); print(json.dumps(report)); print('REPORT_END')
