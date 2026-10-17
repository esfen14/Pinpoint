"""Exercise the action foreign key on populated, disposable multi-bind SQLite databases."""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.getcwd())

with tempfile.TemporaryDirectory() as folder:
    system_path = os.path.join(folder, 'system.db')
    history_path = os.path.join(folder, 'history.db')
    os.environ['DATABASE_URL'] = 'sqlite:///' + system_path
    os.environ['SECRET_KEY'] = 'isolated-migration-test'
    import config
    config.Config.SQLALCHEMY_BINDS = {'history': 'sqlite:///' + history_path}
    import flask_migrate
    from app import app

    with app.app_context():
        flask_migrate.upgrade(directory='migrations', revision='c7a1f4d92e60')
    with sqlite3.connect(system_path) as connection:
        connection.execute("INSERT INTO REMEDIATION_ACTION (Id, Name, Action_Type, Scope_Kind, Host_Pattern, Parameters, Enabled, Max_Runs_Per_Hour, Cooldown_Seconds, Version, Updated_At) VALUES (1, 'existing', 'RECORD_ONLY', 'HOST', '*', '{}', 1, 2, 600, 1, '2026-01-01')")
        sql = "INSERT INTO REMEDIATION_RUN (Event_Key, Action_Id, Action_Name, Hostname, State, State_Type, Attempt, Received_At, Outcome, Output) VALUES (?, ?, ?, 'web-01', 'DOWN', 'HARD', 3, '2026-01-01', 'SUCCEEDED', 'retained audit')"
        connection.executemany(sql, [('live', 1, 'existing'), ('gone', 999, 'deleted'), ('none', None, 'unmatched')])
    with app.app_context():
        flask_migrate.upgrade(directory='migrations', revision='a182f6c9d301')
    report = {}
    with sqlite3.connect(system_path) as connection:
        connection.execute('PRAGMA foreign_keys=ON')
        report['links'] = connection.execute('SELECT Action_Id FROM REMEDIATION_RUN ORDER BY Id').fetchall()
        report['fk_check'] = connection.execute('PRAGMA foreign_key_check').fetchall()
        report['foreign_keys'] = connection.execute('PRAGMA foreign_key_list(REMEDIATION_RUN)').fetchall()
        try:
            connection.execute(sql, ('invalid', 999, 'missing'))
        except sqlite3.IntegrityError:
            report['invalid_refused'] = True
        else:
            report['invalid_refused'] = False
        connection.execute('DELETE FROM REMEDIATION_ACTION WHERE Id=1')
        report['after_delete'] = connection.execute('SELECT Action_Id, Action_Name, Output FROM REMEDIATION_RUN ORDER BY Id').fetchall()
    with app.app_context():
        flask_migrate.downgrade(directory='migrations', revision='c7a1f4d92e60')
    with sqlite3.connect(system_path) as connection:
        report['downgrade_fk'] = connection.execute('PRAGMA foreign_key_list(REMEDIATION_RUN)').fetchall()
        report['downgrade_rows'] = connection.execute('SELECT COUNT(*) FROM REMEDIATION_RUN').fetchone()[0]
    with app.app_context():
        flask_migrate.upgrade(directory='migrations', revision='a182f6c9d301')
    with sqlite3.connect(system_path) as connection:
        report['reupgrade_rows'] = connection.execute('SELECT COUNT(*) FROM REMEDIATION_RUN').fetchone()[0]
    with sqlite3.connect(history_path) as connection:
        report['history_version'] = connection.execute('SELECT version_num FROM alembic_version').fetchone()[0]
    print('REPORT_BEGIN')
    print(json.dumps(report))
    print('REPORT_END')
