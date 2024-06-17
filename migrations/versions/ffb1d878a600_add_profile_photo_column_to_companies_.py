"""Add profile_photo column to companies table

Revision ID: ffb1d878a600
Revises: 15634b282662
Create Date: 2024-05-31 21:49:28.635289

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ffb1d878a600'
down_revision = '15634b282662'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('profile_photo', sa.String(length=120), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.drop_column('profile_photo')

    # ### end Alembic commands ###
