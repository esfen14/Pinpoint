"""Join the NCPA convergence and data-polling histories.

Revision ID: a129f6d23901
Revises: f129a79e6301, f6d2c8a1b390

Keep both published heads and their applied ancestry intact. The normal
multi-bind upgrade applies whichever branch is missing before this no-op
join; existing port, interface, recipient and polling values are preserved.
"""

revision = 'a129f6d23901'
down_revision = ('f129a79e6301', 'f6d2c8a1b390')
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()[f'upgrade_{engine_name}']()


def downgrade(engine_name):
    globals()[f'downgrade_{engine_name}']()


def upgrade_():
    pass


def downgrade_():
    pass


def upgrade_history():
    pass


def downgrade_history():
    pass
