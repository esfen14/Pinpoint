"""allow the restart_local_service remediation action type

REMEDIATION_ACTION.Action_Type is an Enum column. This widens it from RECORD_ONLY to
RECORD_ONLY and RESTART_LOCAL_SERVICE (the stored value is the longer member name). No rows
change. The downgrade deletes actions of the new type (the older schema cannot hold them) and
narrows the column again.

history.db is not touched.

Revision ID: b8e3d5f2a417
Revises: a4c8e1b7d933
"""
from alembic import op
import sqlalchemy as sa

revision = 'b8e3d5f2a417'
down_revision = 'a4c8e1b7d933'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    with op.batch_alter_table('REMEDIATION_ACTION', schema=None) as batch_op:
        batch_op.alter_column(
            'Action_Type',
            existing_type=sa.Enum('RECORD_ONLY', name='remediationactiontype'),
            type_=sa.Enum('RECORD_ONLY', 'RESTART_LOCAL_SERVICE', name='remediationactiontype'),
            existing_nullable=False)


def downgrade_():
    bind = op.get_bind()
    bind.execute(sa.text(
        "DELETE FROM REMEDIATION_RUN WHERE Action_Id IN "
        "(SELECT Id FROM REMEDIATION_ACTION WHERE Action_Type = 'RESTART_LOCAL_SERVICE')"))
    bind.execute(sa.text("DELETE FROM REMEDIATION_ACTION WHERE Action_Type = 'RESTART_LOCAL_SERVICE'"))
    with op.batch_alter_table('REMEDIATION_ACTION', schema=None) as batch_op:
        batch_op.alter_column(
            'Action_Type',
            existing_type=sa.Enum('RECORD_ONLY', 'RESTART_LOCAL_SERVICE', name='remediationactiontype'),
            type_=sa.Enum('RECORD_ONLY', name='remediationactiontype'),
            existing_nullable=False)


def upgrade_history():
    pass


def downgrade_history():
    pass
