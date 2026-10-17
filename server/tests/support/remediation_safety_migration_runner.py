"""
Runs the remediation safety controls migration (f155a3c7d2b1) against a throwaway database and
prints a JSON report. Launched in a subprocess by test_remediation_migration.py.

Usage (from server/): python tests/support/remediation_safety_migration_runner.py
"""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.getcwd())

tmp = tempfile.mkdtemp()
sysdb = os.path.join(tmp, "sys.db").replace("\\", "/")
histdb = os.path.join(tmp, "hist.db").replace("\\", "/")
os.environ["DATABASE_URL"] = "sqlite:///" + sysdb
os.environ["SECRET_KEY"] = "x"

import config  # noqa: E402

config.Config.SQLALCHEMY_BINDS = {"history": "sqlite:///" + histdb}

import flask_migrate  # noqa: E402
from app import app  # noqa: E402

BEFORE = "a182f6c9d301"
TARGET = "f155a3c7d2b1"
report = {}

ACTION = (
    "insert into REMEDIATION_ACTION (Name, Action_Type, Scope_Kind, Host_Pattern, Service_Pattern,"
    " Parameters, Enabled, Max_Runs_Per_Hour, Cooldown_Seconds, Version, Updated_At)"
    " values ('keep', 'RECORD_ONLY', 'SERVICE', 'h', 's', '{}', 1, 2, 600, 1, '2026-01-01')"
)
RUN = (
    "insert into REMEDIATION_RUN (Event_Key, Action_Id, Action_Name, Hostname, Service, State,"
    " State_Type, Attempt, Received_At, Outcome) values (?, 1, 'keep', 'h', 's', 'CRITICAL',"
    " 'HARD', 3, '2026-01-01', ?)"
)


def columns(conn, table):
    return [r[1] for r in conn.execute(f"pragma table_info({table})")]


def tables(conn):
    return sorted(r[0] for r in conn.execute(
        "select name from sqlite_master where type='table' and name like 'REMEDIATION_%'"))


with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=BEFORE)
c = sqlite3.connect(sysdb)
# Fill every required column of the settings row, whatever this revision calls them.
required = {"Id": 1, "Updated_At": "2026-01-01", "Version": 1}
for _cid, name, kind, notnull, default, _pk in c.execute("pragma table_info(SYSTEM_SETTINGS)").fetchall():
    if notnull and default is None and name not in required:
        required[name] = "weekly" if "CHAR" in kind.upper() else 0
c.execute(
    "insert into SYSTEM_SETTINGS (%s) values (%s)" % (", ".join(required), ", ".join("?" * len(required))),
    list(required.values()))
c.execute(ACTION)
c.execute(RUN, ("old", "SUCCEEDED"))
c.commit()
report["tables_before"] = tables(c)
report["settings_columns_before"] = columns(c, "SYSTEM_SETTINGS")
c.close()

with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=TARGET)
c = sqlite3.connect(sysdb)
report["version"] = c.execute("select version_num from alembic_version").fetchall()
report["tables_after"] = tables(c)
report["settings_columns_after"] = columns(c, "SYSTEM_SETTINGS")
report["action_columns_after"] = columns(c, "REMEDIATION_ACTION")
report["state_columns"] = columns(c, "REMEDIATION_CONSUMER_STATE")
report["settings_defaults"] = c.execute(
    "select Remediation_Enabled, Remediation_Retention_Days from SYSTEM_SETTINGS").fetchall()
report["action_default"] = c.execute("select Run_When_Acknowledged from REMEDIATION_ACTION").fetchall()
report["runs_kept"] = c.execute("select count(*) from REMEDIATION_RUN").fetchone()[0]
accepted = []
for n, outcome in enumerate(("SKIPPED_KILL_SWITCH", "SKIPPED_MAINTENANCE", "SKIPPED_DOWNTIME",
                             "SKIPPED_ACKNOWLEDGED")):
    c.execute(RUN, (f"new{n}", outcome))
    accepted.append(outcome)
c.commit()
report["new_outcomes_accepted"] = accepted
c.close()

with app.app_context():
    flask_migrate.downgrade(directory="migrations", revision=BEFORE)
c = sqlite3.connect(sysdb)
report["version_after_downgrade"] = c.execute("select version_num from alembic_version").fetchall()
report["tables_after_downgrade"] = tables(c)
report["settings_columns_after_downgrade"] = columns(c, "SYSTEM_SETTINGS")
report["action_columns_after_downgrade"] = columns(c, "REMEDIATION_ACTION")
report["runs_after_downgrade"] = sorted(
    r[0] for r in c.execute("select Outcome from REMEDIATION_RUN"))
c.close()

with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=TARGET)
c = sqlite3.connect(sysdb)
report["version_after_reupgrade"] = c.execute("select version_num from alembic_version").fetchall()
report["tables_after_reupgrade"] = tables(c)
c.close()

print("REPORT_BEGIN")
print(json.dumps(report))
print("REPORT_END")
