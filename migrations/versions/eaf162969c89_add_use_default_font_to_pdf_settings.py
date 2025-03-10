"""add use_default_font to pdf_settings

Revision ID: eaf162969c89
Revises: e0424da3c525
Create Date: 2025-03-10 12:45:59.140657

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eaf162969c89'
down_revision = 'e0424da3c525'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pdf_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('use_default_font', sa.Boolean(), nullable=False, server_default=sa.true()))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pdf_settings', schema=None) as batch_op:
        batch_op.drop_column('use_default_font')

    # ### end Alembic commands ###
