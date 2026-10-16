"""Exercise the parent migration on populated private databases; never installed data."""
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
    before, target = 'a129f6d23901', 'b117d9a2c041'
    def migrate(revision, down=False):
        with app.app_context():
            (flask_migrate.downgrade if down else flask_migrate.upgrade)(directory='migrations', revision=revision)
    def populate(conn, table, overrides):
        values = dict(overrides)
        for _, name, kind, required, default, primary in conn.execute(f'PRAGMA table_info("{table}")'):
            if name not in values and required and default is None:
                values[name] = '2026-01-01' if 'DATE' in kind else 'fixture' if 'CHAR' in kind else 1
        fields = ', '.join('"' + name + '"' for name in values)
        conn.execute(f'INSERT INTO "{table}" ({fields}) VALUES ({", ".join("?" for _ in values)})', list(values.values()))
    migrate(before)
    with sqlite3.connect(system_path) as conn:
        populate(conn, 'ROLE', {'RoleID':1, 'Name':'Administrator'})
        populate(conn, 'USER', {'UserID':1, 'RoleID':1, 'Email':'existing@example.com', 'Status':'ACTIVE'})
        populate(conn, 'ACTIVITY_LOG', {'LogID':1, 'UserID':1})
        populate(conn, 'NETWORK_DISCOVERY_STATUS', {'DiscoveryStatusID':1, 'LogID':1, 'Status':'SUCCESS'})
        for i in range(1,4):
            populate(conn, 'NETWORK_DISCOVERY', {'NetDiscoveryID':i, 'DiscoveryStatusID':1, 'IP_Address':f'10.77.0.{i+2}', 'Network':'10.77.0.0/28', 'Nagios_Host_Name':f'legacy-{i}', 'Device_State':'ACTIVE'})
    with sqlite3.connect(history_path) as conn:
        schema = list(conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name != 'alembic_version' ORDER BY name"))
    migrate(target)
    report = {}
    with sqlite3.connect(system_path) as conn:
        conn.execute('PRAGMA foreign_keys=ON')
        report['empty'] = conn.execute('SELECT count(*) FROM DEVICE_PARENT').fetchone()[0]
        conn.executemany('INSERT INTO DEVICE_PARENT (Child_ID,Parent_ID) VALUES (?,?)', [(1,2),(1,3)])
        conn.commit()
        rejected=[]
        for pair in [(1,2),(1,1),(1,999),(999,2)]:
            try: conn.execute('INSERT INTO DEVICE_PARENT (Child_ID,Parent_ID) VALUES (?,?)',pair)
            except sqlite3.IntegrityError: rejected.append(pair)
            conn.rollback()
        report['rejected']=rejected
        report['pairs']=conn.execute('SELECT Child_ID,Parent_ID FROM DEVICE_PARENT ORDER BY 1,2').fetchall()
    with sqlite3.connect(history_path) as conn:
        report['history_unchanged']=schema==list(conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name != 'alembic_version' ORDER BY name"))
        report['history_version']=conn.execute('SELECT version_num FROM alembic_version').fetchall()
    migrate(before,down=True)
    with sqlite3.connect(system_path) as conn:
        report['removed']=conn.execute("SELECT name FROM sqlite_master WHERE name='DEVICE_PARENT'").fetchall()==[]
        report['devices']=conn.execute('SELECT Nagios_Host_Name FROM NETWORK_DISCOVERY ORDER BY 1').fetchall()
    migrate(target)
    with sqlite3.connect(system_path) as conn:
        report['reupgrade_empty']=conn.execute('SELECT count(*) FROM DEVICE_PARENT').fetchone()[0]
print('REPORT_BEGIN'); print(json.dumps(report)); print('REPORT_END')
