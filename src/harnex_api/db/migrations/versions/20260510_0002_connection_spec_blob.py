"""connection spec_blob column

Revision ID: 20260510_0002
Revises: 20260507_0001
Create Date: 2026-05-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260510_0002"
down_revision: str | None = "20260507_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "connections",
        sa.Column("spec_blob", sa.LargeBinary(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("connections", "spec_blob")
