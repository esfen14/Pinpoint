"""Exercise either prior head and a merge roundtrip on private throwaway databases."""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.getcwd())
starting_head = sys.argv[1]
assert starting_head in ("7db78f308ee5", "b7d3f1a9c264")
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


upgrade(starting_head)
with sqlite3.connect(sysdb) as conn:
    conn.execute('INSERT INTO NCPA_DEPLOYMENT (NCPADeployID, Agent_Status, NetworkDiscoveryID) VALUES (1, "DEPLOYED", 1)')
    if starting_head == "7db78f308ee5":
        conn.execute('UPDATE NCPA_DEPLOYMENT SET Port=5703 WHERE NCPADeployID=1')
    else:
        conn.execute("INSERT INTO DEVICE_INTERFACE (If_Index,Name,Monitored,Present,Last_Seen_At,NetDiscoveryID) VALUES (1,'eth-test',1,1,'2026-01-01',1)")
with sqlite3.connect(histdb) as conn:
    conn.execute("CREATE TABLE merge_test_marker (value TEXT)")
    conn.execute("INSERT INTO merge_test_marker VALUES ('preserved')")
upgrade("head")
with sqlite3.connect(sysdb) as conn:
    if starting_head != "7db78f308ee5":
        assert conn.execute('SELECT Port FROM NCPA_DEPLOYMENT').fetchone()[0] == int(config.Config.NCPA_PORT)
        conn.execute('UPDATE NCPA_DEPLOYMENT SET Port=5703 WHERE NCPADeployID=1')
    else:
        conn.execute("INSERT INTO DEVICE_INTERFACE (If_Index,Name,Monitored,Present,Last_Seen_At,NetDiscoveryID) VALUES (1,'eth-test',1,1,'2026-01-01',1)")
alembic_config = Config()
alembic_config.set_main_option("script_location", "migrations")
report = {
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
report["roundtrip_port"] = read(sysdb, "SELECT Port FROM NCPA_DEPLOYMENT")[0][0]
report["roundtrip_interface"] = read(sysdb, "SELECT Name,Monitored FROM DEVICE_INTERFACE")[0]
print("REPORT_BEGIN" + json.dumps(report) + "REPORT_END")
workspace.cleanup()
