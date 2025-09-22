"""add_web_search_metadata_to_lesson_plans

Revision ID: eef7f1b555f3
Revises: 7ee85c7e5fcc
Create Date: 2025-09-22 22:11:25.990203

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eef7f1b555f3'
down_revision = '7ee85c7e5fcc'
branch_labels = None
depends_on = None


def upgrade():
    # 添加web_search_info字段到lesson_plans表
    op.add_column('lesson_plans', sa.Column('web_search_info', sa.JSON(), nullable=True, comment='联网搜索结果信息'))


def downgrade():
    # 删除web_search_info字段
    op.drop_column('lesson_plans', 'web_search_info')