# `server/migrations/` — database schema migrations

Alembic migrations managed through Flask-Migrate, configured as
**multi-database**: one revision covers both `system.db` and `history.db`.
`versions/` holds one file per revision; `env.py`, `alembic.ini` and
`script.py.mako` are the generated Flask-Migrate scaffolding. The older
`README` file in this folder is that scaffolding's one-line stub.

Who runs it: developers create revisions; the installer and operators apply
them. Every model change must ship with a migration in the same commit.

Run from `server/` with the virtual environment active:

```bash
flask db migrate --multidb -m "describe the change"   # create a revision from the models
flask db upgrade --multidb                            # apply to both databases
flask db current                                      # show the applied revision
```

Review each generated file by hand: SQLite cannot alter some columns in place,
and autogenerate can miss renames. Never edit an applied revision; add a new one.

Back up both databases before upgrading a real server. A server built earlier
with `db.create_all()` needs `flask db stamp head` once before upgrading; see
[Database setup](../../README.md#database-setup). Backup and recovery:
[`server/README.md`](../README.md#database-layout) and
[Backup and restore](../../docs/manuals/Backup_and_Restore.md).
