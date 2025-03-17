"""Add car insurance model

Revision ID: 58421c3fa678
Revises: be6420278a8e
Create Date: 2025-03-17 10:59:46.288543

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '58421c3fa678'
down_revision = 'be6420278a8e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('car_insurance',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('car_id', sa.Integer(), nullable=False, comment='车辆ID'),
    sa.Column('plate_number', sa.String(length=20), nullable=False, comment='车牌号'),
    sa.Column('car_type', sa.String(length=100), nullable=True, comment='车型'),
    sa.Column('amount', sa.Float(), nullable=False, comment='保险金额'),
    sa.Column('insurance_start_date', sa.Date(), nullable=False, comment='保险开始日期'),
    sa.Column('insurance_end_date', sa.Date(), nullable=False, comment='保险结束日期'),
    sa.Column('renewal_date', sa.Date(), nullable=False, comment='续保日期'),
    sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
    sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
    sa.Column('updated_by', sa.Integer(), nullable=True, comment='更新人ID'),
    sa.ForeignKeyConstraint(['car_id'], ['official_cars.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('car_insurance')
    # ### end Alembic commands ###
