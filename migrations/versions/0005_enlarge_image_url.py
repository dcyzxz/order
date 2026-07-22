"""enlarge image_url columns for base64

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("dishes", "image_url", type_=sa.Text(), existing_type=sa.String(512), nullable=True)
    op.alter_column("pending_dishes", "image_url", type_=sa.Text(), existing_type=sa.String(512), nullable=True)


def downgrade() -> None:
    op.alter_column("dishes", "image_url", type_=sa.String(512), existing_type=sa.Text(), nullable=True)
    op.alter_column("pending_dishes", "image_url", type_=sa.String(512), existing_type=sa.Text(), nullable=True)
