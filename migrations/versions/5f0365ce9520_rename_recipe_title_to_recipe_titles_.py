"""Rename recipe_title to recipe_titles and handle multiple titles

Revision ID: 5f0365ce9520
Revises: 70346cf3588d
Create Date: 2025-06-21 18:37:00.223510

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f0365ce9520'
down_revision = '70346cf3588d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('shopping_list_item', schema=None) as batch_op:
        batch_op.add_column(sa.Column('recipe_titles', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))
        batch_op.alter_column('name',
               existing_type=sa.VARCHAR(length=120),
               type_=sa.String(length=100),
               existing_nullable=False)
        batch_op.alter_column('measure',
               existing_type=sa.VARCHAR(length=80),
               type_=sa.String(length=200),
               existing_nullable=True)
        batch_op.drop_constraint('fk_shopping_list_item_user', type_='foreignkey')
        batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])
        batch_op.drop_column('recipe_title')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('shopping_list_item', schema=None) as batch_op:
        batch_op.add_column(sa.Column('recipe_title', sa.VARCHAR(length=120), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('fk_shopping_list_item_user', 'user', ['user_id'], ['id'], ondelete='CASCADE')
        batch_op.alter_column('measure',
               existing_type=sa.String(length=200),
               type_=sa.VARCHAR(length=80),
               existing_nullable=True)
        batch_op.alter_column('name',
               existing_type=sa.String(length=100),
               type_=sa.VARCHAR(length=120),
               existing_nullable=False)
        batch_op.drop_column('created_at')
        batch_op.drop_column('recipe_titles')

    # ### end Alembic commands ###
