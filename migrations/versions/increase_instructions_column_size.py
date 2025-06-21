"""Increase instructions column size

Revision ID: increase_instructions_column_size
Revises: <previous_revision_id>
Create Date: 2025-06-08 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'inc_instructions'
down_revision = 'd9ece4116d7e'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('recipe', 'instructions', type_=sa.Text())

def downgrade():
    op.alter_column('recipe', 'instructions', type_=sa.String(250)) 