"""add avatar column

Revision ID: add_avatar
Revises: 
Create Date: 2024-06-07 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_avatar'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('avatar', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('user', 'avatar') 