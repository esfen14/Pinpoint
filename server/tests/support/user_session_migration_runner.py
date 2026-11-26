"""Exercise the USER_SESSION migration (a339c5e2d481) on private databases; never installed data."""
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
    before, target = 'e153c4a8b2d7', 'a339c5e2d481'
    def migrate(revision, down=False):
        with app.app_context():
            (flask_migrate.downgrade if down else flask_migrate.upgrade)(directory='migrations', revision=revision)
    def tables(path):
        with sqlite3.connect(path) as conn:
            return list(conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name != 'alembic_version' ORDER BY name"))
    migrate(before)
    history = tables(history_path)
    migrate(target)
    report = {}
    with sqlite3.connect(system_path) as conn:
        report['columns'] = [row[1] for row in conn.execute('PRAGMA table_info("USER_SESSION")')]
        report['indexed'] = [conn.execute(f'PRAGMA index_info("{row[1]}")').fetchone()[2]
                             for row in conn.execute('PRAGMA index_list("USER_SESSION")') if row[3] == 'c']
    report['history_unchanged'] = history == tables(history_path)
    migrate(before, down=True)
    report['removed'] = 'USER_SESSION' not in dict(tables(system_path))
    migrate(target)
    report['restored'] = 'USER_SESSION' in dict(tables(system_path))
print('REPORT_BEGIN'); print(json.dumps(report)); print('REPORT_END')
