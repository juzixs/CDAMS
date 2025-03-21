"""Add new fields to vehicle_exit table

Revision ID: 9f89fe7b5e1a
Revises: 5bf31819c552
Create Date: 2025-03-12 14:48:01.206348

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f89fe7b5e1a'
down_revision = '5bf31819c552'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('vehicle_exit', schema=None) as batch_op:
        batch_op.add_column(sa.Column('department', sa.String(length=100), nullable=True, comment='申请部门'))
        batch_op.add_column(sa.Column('initiator', sa.String(length=50), nullable=True, comment='发起人'))
        batch_op.add_column(sa.Column('certificate_number', sa.String(length=50), nullable=True, comment='出门证编号'))
        batch_op.add_column(sa.Column('vehicle_type', sa.String(length=20), nullable=True, comment='车型：truck（货车）, tractor（拖拉机）, express（快递）, other（其他）'))
        batch_op.add_column(sa.Column('logistics_type', sa.String(length=20), nullable=True, comment='物流方式：company（公司自有车辆）, logistics（物流公司车辆）, outsourcing（外协车辆）'))
        batch_op.add_column(sa.Column('logistics_company', sa.String(length=100), nullable=True, comment='物流公司名称'))
        batch_op.add_column(sa.Column('logistics_number', sa.String(length=50), nullable=True, comment='物流单号'))
        batch_op.add_column(sa.Column('item_category', sa.String(length=20), nullable=True, comment='出厂物品分类：product（产成品交付）, outsourcing（外协）, material（园区物料周转）, other（其他）'))
        batch_op.add_column(sa.Column('confirmed_exit_time', sa.DateTime(), nullable=True, comment='确认出厂日期（门卫签字日期）'))
        batch_op.add_column(sa.Column('reviewer', sa.String(length=50), nullable=True, comment='审核人'))
        batch_op.add_column(sa.Column('issuer', sa.String(length=50), nullable=True, comment='发放人'))
        batch_op.add_column(sa.Column('guard', sa.String(length=50), nullable=True, comment='门卫'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('vehicle_exit', schema=None) as batch_op:
        batch_op.drop_column('guard')
        batch_op.drop_column('issuer')
        batch_op.drop_column('reviewer')
        batch_op.drop_column('confirmed_exit_time')
        batch_op.drop_column('item_category')
        batch_op.drop_column('logistics_number')
        batch_op.drop_column('logistics_company')
        batch_op.drop_column('logistics_type')
        batch_op.drop_column('vehicle_type')
        batch_op.drop_column('certificate_number')
        batch_op.drop_column('initiator')
        batch_op.drop_column('department')

    # ### end Alembic commands ###
