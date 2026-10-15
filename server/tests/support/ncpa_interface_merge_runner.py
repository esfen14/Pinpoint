"""Exercise either prior head and a merge roundtrip on private throwaway databases."""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.getcwd())
starting_head = sys.argv[1]
assert starting_head in ("7db78f308ee5", "b7d3f1a9c264", "e4a129c7b630", "e79b7d3c2641", "f129a79e6301", "f6d2c8a1b390", "cd74e5f8a2d5", "e4a7c1d9b305")
has_port = starting_head in ("7db78f308ee5", "e4a129c7b630", "f129a79e6301", "e4a7c1d9b305")
has_recipients = starting_head in ("e79b7d3c2641", "f129a79e6301", "f6d2c8a1b390", "cd74e5f8a2d5", "e4a7c1d9b305")
has_polling = starting_head in ("f6d2c8a1b390", "e4a7c1d9b305")
new_merge_parent = starting_head in ("cd74e5f8a2d5", "e4a7c1d9b305")
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


def feature_rows():
    """Snapshot only existing feature tables so upgrade can add the other branch."""
    with sqlite3.connect(sysdb) as conn:
        names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        return {name: conn.execute(f'SELECT * FROM "{name}" ORDER BY 1').fetchall()
                for name in ('ESCALATION', 'REMEDIATION_ACTION', 'REMEDIATION_RUN') if name in names}


def populate_features(conn, escalation=False, remediation=False):
    """Persist representative valid choices/runs for merge data-preservation checks."""
    if escalation:
        conn.execute("INSERT INTO ESCALATION VALUES (1, 2, 5, 10, 'pinpoint_host_1', 1)")
    if remediation:
        populate(conn, 'REMEDIATION_ACTION', {'Id': 1, 'Name': 'Existing action',
                 'Action_Type': 'RECORD_ONLY', 'Scope_Kind': 'SERVICE',
                 'Host_Pattern': 'existing', 'Service_Pattern': 'SSH', 'Parameters': '{}'})
        populate(conn, 'REMEDIATION_RUN', {'Id': 1, 'Action_Id': 1, 'Event_Key': 'existing-event',
                 'Action_Name': 'Existing action', 'Hostname': 'existing', 'Service': 'SSH',
                 'State': 'CRITICAL', 'State_Type': 'HARD', 'Outcome': 'SUCCEEDED'})


upgrade(starting_head)
with sqlite3.connect(sysdb) as conn:
    populate(conn, 'SYSTEM_SETTINGS', {})
    if has_polling:
        conn.execute('UPDATE SYSTEM_SETTINGS SET Data_Polling_Interval=120')
    populate(conn, 'ROLE', {'RoleID': 1, 'Name': 'Administrator'})
    populate(conn, 'USER', {'UserID': 1, 'RoleID': 1, 'Email': 'fixture@example.com', 'Status': 'ACTIVE'})
    populate(conn, 'ACTIVITY_LOG', {'LogID': 1, 'UserID': 1})
    populate(conn, 'NETWORK_DISCOVERY_STATUS', {'DiscoveryStatusID': 1, 'LogID': 1, 'Status': 'SUCCESS'})
    populate(conn, 'NETWORK_DISCOVERY', {'NetDiscoveryID': 1, 'DiscoveryStatusID': 1,
             'IP_Address': '10.77.0.2', 'Network': '10.77.0.0/28', 'Nagios_Host_Name': 'existing', 'Device_State': 'ACTIVE'})
    if has_recipients:
        conn.execute('INSERT INTO HOST_ALERT_RECIPIENT VALUES (1, 1)')
    conn.execute('INSERT INTO NCPA_DEPLOYMENT (NCPADeployID, Agent_Status, NetworkDiscoveryID) VALUES (1, "DEPLOYED", 1)')
    if has_port:
        conn.execute('UPDATE NCPA_DEPLOYMENT SET Port=5703 WHERE NCPADeployID=1')
    if has_interfaces:
        conn.execute("INSERT INTO DEVICE_INTERFACE (If_Index,Name,Monitored,Present,Last_Seen_At,NetDiscoveryID) VALUES (1,'eth-test',1,1,'2026-01-01',1)")
if new_merge_parent:
    with sqlite3.connect(sysdb) as conn:
        populate_features(conn, escalation=starting_head == 'cd74e5f8a2d5',
                          remediation=starting_head == 'e4a7c1d9b305')
existing_features = feature_rows() if new_merge_parent else {}
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
    if not has_recipients:
        conn.execute('INSERT INTO HOST_ALERT_RECIPIENT VALUES (1, 1)')
    if not has_polling:
        assert conn.execute('SELECT Data_Polling_Interval FROM SYSTEM_SETTINGS').fetchone()[0] == 60
        conn.execute('UPDATE SYSTEM_SETTINGS SET Data_Polling_Interval=120')
    assert not conn.execute('PRAGMA foreign_key_check').fetchall()
if new_merge_parent:
    assert all(feature_rows()[name] == rows for name, rows in existing_features.items())
    with sqlite3.connect(sysdb) as conn:
        populate_features(conn, escalation=starting_head != 'cd74e5f8a2d5',
                          remediation=starting_head != 'e4a7c1d9b305')
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()
joined_features = feature_rows() if new_merge_parent else {}
alembic_config = Config()
alembic_config.set_main_option("script_location", "migrations")
report = {
    "polling": read(sysdb, "SELECT Data_Polling_Interval FROM SYSTEM_SETTINGS")[0][0],
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
    flask_migrate.downgrade(directory="migrations", revision=starting_head if new_merge_parent else "7db78f308ee5")
if new_merge_parent:
    assert feature_rows() == joined_features
upgrade("head")
report['existing_feature_rows_preserved'] = all(joined_features[name] == rows for name, rows in existing_features.items())
report['merge_roundtrip_preserves_features'] = feature_rows() == joined_features if new_merge_parent else True
report["roundtrip_polling"] = read(sysdb, "SELECT Data_Polling_Interval FROM SYSTEM_SETTINGS")[0][0]
report["roundtrip_recipient"] = read(sysdb, "SELECT * FROM HOST_ALERT_RECIPIENT")
report["roundtrip_port"] = read(sysdb, "SELECT Port FROM NCPA_DEPLOYMENT")[0][0]
report["roundtrip_interface"] = read(sysdb, "SELECT Name,Monitored FROM DEVICE_INTERFACE")[0]
print("REPORT_BEGIN" + json.dumps(report) + "REPORT_END")
workspace.cleanup()
