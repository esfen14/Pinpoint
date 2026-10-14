"""
Runs the flap detection settings migration (c5e2a8f4d716)
against throwaway databases and prints a JSON report. Not a test itself: it is
launched in a subprocess by test_flap_settings_migration.py because Alembic needs
a Flask app configured for temporary databases before "app" is imported.

Usage (from server/): python tests/support/flap_settings_migration_runner.py
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

BEFORE = "b7d3f1a9c8e5"
TARGET = "c5e2a8f4d716"
report = {}


def columns(conn):
    return [row[1] for row in conn.execute("pragma table_info(SYSTEM_SETTINGS)")]


def flap(conn):
    return conn.execute("select Check_Interval, Flap_Detection_Enabled, Flap_Low_Threshold, Flap_High_Threshold from SYSTEM_SETTINGS").fetchall()


def insert_settings_row(conn):
    """One existing settings row, filling every NOT NULL column that has no default."""
    names, values = [], []
    for _cid, name, ctype, notnull, default, pk in conn.execute("pragma table_info(SYSTEM_SETTINGS)"):
        if pk:
            names.append(name)
            values.append(1)
        elif notnull and default is None:
            names.append(name)
            upper = ctype.upper()
            values.append("2026-01-01" if "DATE" in upper else "x" if "CHAR" in upper else 1)
    conn.execute(f"insert into SYSTEM_SETTINGS ({', '.join(names)}) values ({', '.join('?' * len(values))})", values)


with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=BEFORE)

c = sqlite3.connect(sysdb)
report["columns_before"] = columns(c)
insert_settings_row(c)
c.execute("update SYSTEM_SETTINGS set Check_Interval = 10")
c.commit()
c.close()

with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=TARGET)
c = sqlite3.connect(sysdb)
report["version"] = c.execute("select version_num from alembic_version").fetchall()
report["columns_after"] = columns(c)
report["flap_after_upgrade"] = flap(c)
c.close()

with app.app_context():
    flask_migrate.downgrade(directory="migrations", revision=BEFORE)
c = sqlite3.connect(sysdb)
report["columns_after_downgrade"] = columns(c)
report["check_interval_after_downgrade"] = c.execute("select Check_Interval from SYSTEM_SETTINGS").fetchall()
c.close()

with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=TARGET)
c = sqlite3.connect(sysdb)
report["version_after_reupgrade"] = c.execute("select version_num from alembic_version").fetchall()
report["flap_after_reupgrade"] = flap(c)
c.close()

print("REPORT_BEGIN")
print(json.dumps(report))
print("REPORT_END")
