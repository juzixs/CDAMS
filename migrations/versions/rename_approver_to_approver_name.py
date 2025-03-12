"""Add approver_name column to VehicleExit model

Revision ID: rename_approver_to_approver_name
Revises: 9f89fe7b5e1a
Create Date: 2025-03-12 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rename_approver_to_approver_name'
down_revision = '9f89fe7b5e1a'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 approver_name 列
    op.add_column('vehicle_exit', sa.Column('approver_name', sa.String(50), nullable=True))


def downgrade():
    # 删除 approver_name 列
    op.drop_column('vehicle_exit', 'approver_name') 