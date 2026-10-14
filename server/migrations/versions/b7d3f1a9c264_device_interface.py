"""add device interfaces for bandwidth monitoring

DEVICE_INTERFACE holds the interfaces SNMP reports for a device and whether an
administrator chose to monitor each one (an in and an out octet Nagios service).
With no rows nothing changes: the generated Nagios config is identical to before.
The downgrade drops the table. history.db is not touched.

Revision ID: b7d3f1a9c264
Revises: 143c48cd6663
Create Date: 2026-10-14 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7d3f1a9c264'
down_revision = '143c48cd6663'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    op.create_table('DEVICE_INTERFACE',
    sa.Column('DeviceInterfaceID', sa.Integer(), nullable=False),
    sa.Column('If_Index', sa.Integer(), nullable=False),
    sa.Column('Name', sa.String(length=100), nullable=False),
    sa.Column('Speed_Bps', sa.BigInteger(), nullable=True),
    sa.Column('Admin_Status', sa.String(length=20), nullable=True),
    sa.Column('Oper_Status', sa.String(length=20), nullable=True),
    sa.Column('Monitored', sa.Boolean(), nullable=False),
    sa.Column('Present', sa.Boolean(), nullable=False),
    sa.Column('Last_Seen_At', sa.DateTime(), nullable=False),
    sa.Column('NetDiscoveryID', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['NetDiscoveryID'], ['NETWORK_DISCOVERY.NetDiscoveryID'], ),
    sa.PrimaryKeyConstraint('DeviceInterfaceID'),
    sa.UniqueConstraint('NetDiscoveryID', 'If_Index', name='uq_device_interface_index')
    )
    with op.batch_alter_table('DEVICE_INTERFACE', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_DEVICE_INTERFACE_NetDiscoveryID'), ['NetDiscoveryID'], unique=False)


def downgrade_():
    with op.batch_alter_table('DEVICE_INTERFACE', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_DEVICE_INTERFACE_NetDiscoveryID'))

    op.drop_table('DEVICE_INTERFACE')


def upgrade_history():
    pass


def downgrade_history():
    pass
