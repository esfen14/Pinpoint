"""add the resource forecast table

RESOURCE_FORECAST holds the latest straight-line forecast of when a disk or memory metric
reaches its threshold, one row per host, service and metric, replaced on every run (see
app/forecast.py). A series too new to forecast is a row of Kind 'insufficient' with no estimate. With no rows nothing changes. The downgrade drops the table. history.db is
not touched. No permission is added: the route reuses system.dashboard and system.services.

Revision ID: b7e2a9c4d518
Revises: d117f3b8a053
Create Date: 2026-10-17 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7e2a9c4d518'
down_revision = 'd117f3b8a053'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    op.create_table('RESOURCE_FORECAST',
    sa.Column('ForecastID', sa.Integer(), nullable=False),
    sa.Column('Hostname', sa.String(length=100), nullable=False),
    sa.Column('Service', sa.String(length=150), nullable=False),
    sa.Column('Metric', sa.String(length=50), nullable=False),
    sa.Column('Kind', sa.String(length=12), nullable=False),
    sa.Column('Threshold', sa.Float(), nullable=True),
    sa.Column('Crossing_At', sa.DateTime(), nullable=True),
    sa.Column('Slope_Per_Hour', sa.Float(), nullable=True),
    sa.Column('R_Squared', sa.Float(), nullable=True),
    sa.Column('Sample_Count', sa.Integer(), nullable=False),
    sa.Column('Window_Hours', sa.Float(), nullable=False),
    sa.Column('Current_Value', sa.Float(), nullable=True),
    sa.Column('Unit', sa.String(length=5), nullable=True),
    sa.Column('Computed_At', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('ForecastID'),
    sa.UniqueConstraint('Hostname', 'Service', 'Metric', name='uq_resource_forecast_metric')
    )
    with op.batch_alter_table('RESOURCE_FORECAST', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_RESOURCE_FORECAST_Crossing_At'), ['Crossing_At'], unique=False)
        batch_op.create_index(batch_op.f('ix_RESOURCE_FORECAST_Hostname'), ['Hostname'], unique=False)


def downgrade_():
    with op.batch_alter_table('RESOURCE_FORECAST', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_RESOURCE_FORECAST_Hostname'))
        batch_op.drop_index(batch_op.f('ix_RESOURCE_FORECAST_Crossing_At'))

    op.drop_table('RESOURCE_FORECAST')


def upgrade_history():
    pass


def downgrade_history():
    pass
