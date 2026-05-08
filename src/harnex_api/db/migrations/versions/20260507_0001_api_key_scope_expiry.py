"""api key scope + expiry

Revision ID: 20260507_0001
Revises: 20260428_0000
Create Date: 2026-05-07
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260507_0001"
down_revision: str | None = "20260428_0000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "api_keys",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "api_keys",
        sa.Column(
            "scope",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text('\'{"type": "all"}\'::jsonb'),
        ),
    )


def downgrade() -> None:
    op.drop_column("api_keys", "scope")
    op.drop_column("api_keys", "expires_at")
