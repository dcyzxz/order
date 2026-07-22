"""use MEDIUMTEXT for image columns to support large base64

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import MEDIUMTEXT

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("dishes", "image_url", type_=MEDIUMTEXT, existing_type=sa.Text(), nullable=True)
    op.alter_column("pending_dishes", "image_url", type_=MEDIUMTEXT, existing_type=sa.Text(), nullable=True)
    op.alter_column("users", "avatar_url", type_=MEDIUMTEXT, existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    op.alter_column("dishes", "image_url", type_=sa.Text(), existing_type=MEDIUMTEXT, nullable=True)
    op.alter_column("pending_dishes", "image_url", type_=sa.Text(), existing_type=MEDIUMTEXT, nullable=True)
    op.alter_column("users", "avatar_url", type_=sa.Text(), existing_type=MEDIUMTEXT, nullable=True)
