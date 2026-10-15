"""Exercise either prior head and a merge roundtrip on private throwaway databases."""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.getcwd())
starting_head = sys.argv[1]
assert starting_head in ("7db78f308ee5", "b7d3f1a9c264", "e4a129c7b630", "e79b7d3c2641")
has_port = starting_head in ("7db78f308ee5", "e4a129c7b630")
has_interfaces = starting_head != "7db78f308ee5"
workspace = tempfile.TemporaryDirectory()
sysdb = os.path.join(workspace.name, "system.db")
histdb = os.path.join(workspace.name, "history.db")
os.environ["DATABASE_URL"] = "sqlite:///" + sysdb
os.environ["SECRET_KEY"] = "isolated-merge-migration"
import config
config.Config.SQLALCHEMY_BINDS = {"history": "sqlite:///" + histdb}
import flask_migrate
from app import app
from alembic.config import Config
from alembic.script import ScriptDirectory


def upgrade(revision):
    with app.app_context():
        flask_migrate.upgrade(directory="migrations", revision=revision)


def read(path, sql):
    with sqlite3.connect(path) as conn:
        return conn.execute(sql).fetchall()


def populate(conn, table, values):
    """Supply required fixture fields while retaining real foreign-key relationships."""
    values = dict(values)
    for _, name, kind, required, default, _ in conn.execute(f'PRAGMA table_info("{table}")'):
        if name not in values and required and default is None:
            values[name] = '2026-01-01' if 'DATE' in kind else 'fixture' if 'CHAR' in kind else 1
    fields = ', '.join('"' + key + '"' for key in values)
    conn.execute(f'INSERT INTO "{table}" ({fields}) VALUES ({", ".join("?" for _ in values)})', list(values.values()))


upgrade(starting_head)
with sqlite3.connect(sysdb) as conn:
    populate(conn, 'ROLE', {'RoleID': 1, 'Name': 'Administrator'})
    populate(conn, 'USER', {'UserID': 1, 'RoleID': 1, 'Email': 'fixture@example.com', 'Status': 'ACTIVE'})
    populate(conn, 'ACTIVITY_LOG', {'LogID': 1, 'UserID': 1})
    populate(conn, 'NETWORK_DISCOVERY_STATUS', {'DiscoveryStatusID': 1, 'LogID': 1, 'Status': 'SUCCESS'})
    populate(conn, 'NETWORK_DISCOVERY', {'NetDiscoveryID': 1, 'DiscoveryStatusID': 1,
             'IP_Address': '10.77.0.2', 'Network': '10.77.0.0/28', 'Nagios_Host_Name': 'existing', 'Device_State': 'ACTIVE'})
    if starting_head == 'e79b7d3c2641':
        conn.execute('INSERT INTO HOST_ALERT_RECIPIENT VALUES (1, 1)')
    conn.execute('INSERT INTO NCPA_DEPLOYMENT (NCPADeployID, Agent_Status, NetworkDiscoveryID) VALUES (1, "DEPLOYED", 1)')
    if has_port:
        conn.execute('UPDATE NCPA_DEPLOYMENT SET Port=5703 WHERE NCPADeployID=1')
    if has_interfaces:
        conn.execute("INSERT INTO DEVICE_INTERFACE (If_Index,Name,Monitored,Present,Last_Seen_At,NetDiscoveryID) VALUES (1,'eth-test',1,1,'2026-01-01',1)")
with sqlite3.connect(histdb) as conn:
    conn.execute("CREATE TABLE merge_test_marker (value TEXT)")
    conn.execute("INSERT INTO merge_test_marker VALUES ('preserved')")
upgrade("head")
with sqlite3.connect(sysdb) as conn:
    if not has_port:
        assert conn.execute('SELECT Port FROM NCPA_DEPLOYMENT').fetchone()[0] == int(config.Config.NCPA_PORT)
        conn.execute('UPDATE NCPA_DEPLOYMENT SET Port=5703 WHERE NCPADeployID=1')
    if not has_interfaces:
        conn.execute("INSERT INTO DEVICE_INTERFACE (If_Index,Name,Monitored,Present,Last_Seen_At,NetDiscoveryID) VALUES (1,'eth-test',1,1,'2026-01-01',1)")
with sqlite3.connect(sysdb) as conn:
    if starting_head != 'e79b7d3c2641':
        conn.execute('INSERT INTO HOST_ALERT_RECIPIENT VALUES (1, 1)')
    assert not conn.execute('PRAGMA foreign_key_check').fetchall()
alembic_config = Config()
alembic_config.set_main_option("script_location", "migrations")
report = {
    "recipient": read(sysdb, "SELECT * FROM HOST_ALERT_RECIPIENT"),
    "heads": ScriptDirectory.from_config(alembic_config).get_heads(),
    "system_version": read(sysdb, "SELECT version_num FROM alembic_version"),
    "history_version": read(histdb, "SELECT version_num FROM alembic_version"),
    "port": read(sysdb, "SELECT Port FROM NCPA_DEPLOYMENT")[0][0],
    "interface": read(sysdb, "SELECT Name,Monitored FROM DEVICE_INTERFACE")[0],
    "history_marker": read(histdb, "SELECT value FROM merge_test_marker")[0][0],
}
# Downgrade only the no-op join, retaining both schemas/data, then rejoin.
with app.app_context():
    flask_migrate.downgrade(directory="migrations", revision="7db78f308ee5")
upgrade("head")
report["roundtrip_recipient"] = read(sysdb, "SELECT * FROM HOST_ALERT_RECIPIENT")
report["roundtrip_port"] = read(sysdb, "SELECT Port FROM NCPA_DEPLOYMENT")[0][0]
report["roundtrip_interface"] = read(sysdb, "SELECT Name,Monitored FROM DEVICE_INTERFACE")[0]
print("REPORT_BEGIN" + json.dumps(report) + "REPORT_END")
workspace.cleanup()
