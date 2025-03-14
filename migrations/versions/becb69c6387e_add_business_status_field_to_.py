"""add business_status field to OfficialCar model

Revision ID: becb69c6387e
Revises: 7dd8e8535975
Create Date: 2025-03-14 09:20:27.338506

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'becb69c6387e'
down_revision = '7dd8e8535975'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('official_cars', schema=None) as batch_op:
        batch_op.add_column(sa.Column('business_status', sa.String(length=100), nullable=True, comment='使用状况'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('official_cars', schema=None) as batch_op:
        batch_op.drop_column('business_status')

    # ### end Alembic commands ###
