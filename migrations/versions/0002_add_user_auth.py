"""add username, password_hash, role to users

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(64), nullable=True, comment="用户名"))
    op.add_column("users", sa.Column("password_hash", sa.String(128), nullable=True, comment="密码哈希"))
    op.add_column("users", sa.Column("role", sa.String(20), server_default="user", comment="角色: admin/chef/user"))
    op.create_unique_constraint("uq_users_username", "users", ["username"])
    # Make openid nullable
    op.alter_column("users", "openid", existing_type=sa.String(128), nullable=True)


def downgrade() -> None:
    op.drop_constraint("uq_users_username", "users")
    op.drop_column("users", "role")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "username")
    op.alter_column("users", "openid", existing_type=sa.String(128), nullable=False)
