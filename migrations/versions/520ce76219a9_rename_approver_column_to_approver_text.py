"""Rename approver column to approver_text

Revision ID: 520ce76219a9
Revises: 21400eedb5f2
Create Date: 2024-03-13 00:30:03.072246

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '520ce76219a9'
down_revision = '21400eedb5f2'
branch_labels = None
depends_on = None


def upgrade():
    # 使用SQLite，添加新列
    with op.batch_alter_table('vehicle_exit') as batch_op:
        # 添加新列
        batch_op.add_column(sa.Column('approver_text', sa.String(50), nullable=True))


def downgrade():
    # 使用SQLite，删除添加的列
    with op.batch_alter_table('vehicle_exit') as batch_op:
        batch_op.drop_column('approver_text')
