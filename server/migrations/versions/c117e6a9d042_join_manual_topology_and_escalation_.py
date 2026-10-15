"""Join manual topology and escalation remediation histories

Revision ID: c117e6a9d042
Revises: b117d9a2c041, 99f584ed8151
Create Date: 2026-10-15 20:18:40.970928

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c117e6a9d042'
down_revision = ('b117d9a2c041', '99f584ed8151')
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

