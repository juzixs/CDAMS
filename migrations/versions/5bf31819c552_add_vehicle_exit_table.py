"""Add vehicle exit table

Revision ID: 5bf31819c552
Revises: eaf162969c89
Create Date: 2025-03-12 14:32:01.832038

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5bf31819c552'
down_revision = 'eaf162969c89'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('vehicle_exit',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('exit_type', sa.String(length=20), nullable=False, comment='出门类型：outsourcing（外协）或 product（产成品）'),
    sa.Column('plate_number', sa.String(length=20), nullable=False, comment='车牌号'),
    sa.Column('driver_name', sa.String(length=50), nullable=False, comment='驾驶员姓名'),
    sa.Column('id_number', sa.String(length=30), nullable=True, comment='身份证号码'),
    sa.Column('phone', sa.String(length=20), nullable=True, comment='联系电话'),
    sa.Column('company', sa.String(length=100), nullable=True, comment='单位名称'),
    sa.Column('destination', sa.String(length=200), nullable=True, comment='目的地'),
    sa.Column('items', sa.Text(), nullable=True, comment='携带物品'),
    sa.Column('purpose', sa.String(length=200), nullable=True, comment='出门事由'),
    sa.Column('exit_time', sa.DateTime(), nullable=True, comment='出门时间'),
    sa.Column('expected_return_time', sa.DateTime(), nullable=True, comment='预计返回时间'),
    sa.Column('actual_return_time', sa.DateTime(), nullable=True, comment='实际返回时间'),
    sa.Column('status', sa.String(length=20), nullable=True, comment='状态：pending（待审核）, approved（已审核）, completed（已完成）'),
    sa.Column('remarks', sa.Text(), nullable=True, comment='备注'),
    sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
    sa.Column('approved_by', sa.Integer(), nullable=True, comment='审核人ID'),
    sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
    sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('vehicle_exit')
    # ### end Alembic commands ###
