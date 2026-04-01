"""add datagolf_updated_at to fetches

Revision ID: b7c4e9f12a03
Revises: 4938bf64fe7e
Create Date: 2026-04-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c4e9f12a03'
down_revision = '4938bf64fe7e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('fetches', sa.Column('datagolf_updated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column('fetches', 'datagolf_updated_at')
