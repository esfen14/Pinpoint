"""Merge escalation and remediation histories without changing either schema.

Keep both published revision histories intact. Upgrades apply the missing
branch before joining; downgrading this join leaves parent tables and rows
unchanged on both database binds.

Revision ID: 99f584ed8151
Revises: cd74e5f8a2d5, e4a7c1d9b305
Create Date: 2026-10-15 19:38:32.748323

"""

# revision identifiers, used by Alembic.
revision = '99f584ed8151'
down_revision = ('cd74e5f8a2d5', 'e4a7c1d9b305')
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    pass


def downgrade_():
    pass


def upgrade_history():
    pass


def downgrade_history():
    pass
