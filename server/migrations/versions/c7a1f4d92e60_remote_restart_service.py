"""allow the restart_remote_service remediation action and add its per-device settings

REMEDIATION_ACTION.Action_Type is an Enum column, widened here with RESTART_REMOTE_SERVICE.
SSH_CREDENTIALS gains Remote_Restart_Enabled (default false, so no device allows a remote
restart until an administrator turns it on) and Remote_Restart_Services (the per-device list of
units, empty by default). The downgrade deletes actions of the new type, which the older schema
cannot hold, and drops the two columns.

history.db is not touched.

Revision ID: c7a1f4d92e60
Revises: b8e3d5f2a417
"""
from alembic import op
import sqlalchemy as sa

revision = 'c7a1f4d92e60'
down_revision = 'b8e3d5f2a417'
branch_labels = None
depends_on = None

OLD_ENUM = sa.Enum('RECORD_ONLY', 'RESTART_LOCAL_SERVICE', name='remediationactiontype')
NEW_ENUM = sa.Enum('RECORD_ONLY', 'RESTART_LOCAL_SERVICE', 'RESTART_REMOTE_SERVICE', name='remediationactiontype')


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    with op.batch_alter_table('REMEDIATION_ACTION', schema=None) as batch_op:
        batch_op.alter_column('Action_Type', existing_type=OLD_ENUM, type_=NEW_ENUM, existing_nullable=False)
    with op.batch_alter_table('SSH_CREDENTIALS', schema=None) as batch_op:
        batch_op.add_column(sa.Column('Remote_Restart_Enabled', sa.Boolean(), server_default=sa.false(), nullable=False))
        batch_op.add_column(sa.Column('Remote_Restart_Services', sa.JSON(), nullable=True))


def downgrade_():
    bind = op.get_bind()
    bind.execute(sa.text(
        "DELETE FROM REMEDIATION_RUN WHERE Action_Id IN "
        "(SELECT Id FROM REMEDIATION_ACTION WHERE Action_Type = 'RESTART_REMOTE_SERVICE')"))
    bind.execute(sa.text("DELETE FROM REMEDIATION_ACTION WHERE Action_Type = 'RESTART_REMOTE_SERVICE'"))
    with op.batch_alter_table('SSH_CREDENTIALS', schema=None) as batch_op:
        batch_op.drop_column('Remote_Restart_Services')
        batch_op.drop_column('Remote_Restart_Enabled')
    with op.batch_alter_table('REMEDIATION_ACTION', schema=None) as batch_op:
        batch_op.alter_column('Action_Type', existing_type=NEW_ENUM, type_=OLD_ENUM, existing_nullable=False)


def upgrade_history():
    pass


def downgrade_history():
    pass
