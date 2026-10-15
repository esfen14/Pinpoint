"""Exercise the NCPA port migration against isolated SQLite databases."""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.getcwd())
tmp = tempfile.mkdtemp()
sysdb = os.path.join(tmp, "system.db")
histdb = os.path.join(tmp, "history.db")
os.environ["DATABASE_URL"] = "sqlite:///" + sysdb
os.environ["SECRET_KEY"] = "migration-test"

import config
config.Config.SQLALCHEMY_BINDS = {"history": "sqlite:///" + histdb}
import flask_migrate
from app import app

before = "c5e2a8f4d716"
target = "7db78f308ee5"
with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=before)

conn = sqlite3.connect(sysdb)
columns = [row[1] for row in conn.execute("PRAGMA table_info(NCPA_DEPLOYMENT)")]
assert "Port" not in columns
# SQLite permits these rows without a referenced device; the migration only
# transforms NCPA_DEPLOYMENT and should leave unrelated data untouched.
conn.executemany(
    'INSERT INTO NCPA_DEPLOYMENT ("NCPADeployID", "Agent_Status", "NetworkDiscoveryID") VALUES (?, ?, ?)',
    [(1, "DEPLOYED", 1), (2, "FAILED", 2), (3, "PENDING_NCPA", 3)],
)
conn.commit()
conn.close()

with app.app_context():
    flask_migrate.upgrade(directory="migrations", revision=target)
conn = sqlite3.connect(sysdb)
up = conn.execute('SELECT "NCPADeployID", "Port" FROM NCPA_DEPLOYMENT ORDER BY "NCPADeployID"').fetchall()
conn.close()
with app.app_context():
    flask_migrate.downgrade(directory="migrations", revision=before)
conn = sqlite3.connect(sysdb)
down_columns = [row[1] for row in conn.execute("PRAGMA table_info(NCPA_DEPLOYMENT)")]
remaining = conn.execute('SELECT "NCPADeployID", "Agent_Status" FROM NCPA_DEPLOYMENT ORDER BY "NCPADeployID"').fetchall()
conn.close()
print("REPORT_BEGIN" + json.dumps({"up": up, "down_columns": down_columns, "remaining": remaining}) + "REPORT_END")
