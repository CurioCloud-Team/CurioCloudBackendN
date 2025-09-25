"""add landppt_api_key to users table

Revision ID: de7e45761a93
Revises: eef7f1b555f3
Create Date: 2025-09-25 01:36:35.683781

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'de7e45761a93'
down_revision = 'e1ba903ce39a'
branch_labels = None
depends_on = None


def upgrade():
    # 添加landppt_api_key字段到users表
    op.add_column('users', sa.Column('landppt_api_key', sa.String(128), nullable=True, comment='对应的LandPPT API密钥'))


def downgrade():
    # 删除landppt_api_key字段
    op.drop_column('users', 'landppt_api_key')