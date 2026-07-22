"""enlarge avatar_url for base64

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "avatar_url", type_=sa.Text(), existing_type=sa.String(512), nullable=True)


def downgrade() -> None:
    op.alter_column("users", "avatar_url", type_=sa.String(512), existing_type=sa.Text(), nullable=True)
