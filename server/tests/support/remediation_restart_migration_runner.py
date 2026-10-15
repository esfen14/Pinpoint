"""
Runs the restart_local_service migration (b8e3d5f2a417) against a throwaway database and prints
a JSON report. Launched in a subprocess by test_remediation_migration.py.

Usage (from server/): python tests/support/remediation_restart_migration_runner.py
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

BEFORE = "a4c8e1b7d933"
TARGET = "b8e3d5f2a417"
report = {}

ACTION = (
    "insert into REMEDIATION_ACTION (Name, Action_Type, Scope_Kind, Host_Pattern, Service_Pattern,"
    " Parameters, Enabled, Max_Runs_Per_Hour, Cooldown_Seconds, Version, Updated_At)"
    " values (?, ?, 'SERVICE', 'h', 's', '{}', 1, 2, 600, 1, '2026-01-01')"
)


def names(conn):
    return [r[0] for r in conn.execute("select Name from REMEDIATION_ACTION order by Id")]


with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=BEFORE)
c = sqlite3.connect(sysdb)
c.execute(ACTION, ("keep", "RECORD_ONLY"))
c.commit()
c.close()

with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=TARGET)
c = sqlite3.connect(sysdb)
report["version"] = c.execute("select version_num from alembic_version").fetchall()
report["kept_after_upgrade"] = names(c)
c.execute(ACTION, ("restart", "RESTART_LOCAL_SERVICE"))
c.commit()
report["names_with_restart"] = names(c)
c.close()

with app.app_context():
    flask_migrate.downgrade(directory="migrations", revision=BEFORE)
c = sqlite3.connect(sysdb)
report["version_after_downgrade"] = c.execute("select version_num from alembic_version").fetchall()
report["names_after_downgrade"] = names(c)
c.close()

with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=TARGET)
c = sqlite3.connect(sysdb)
report["version_after_reupgrade"] = c.execute("select version_num from alembic_version").fetchall()
report["names_after_reupgrade"] = names(c)
c.close()

print("REPORT_BEGIN")
print(json.dumps(report))
print("REPORT_END")
