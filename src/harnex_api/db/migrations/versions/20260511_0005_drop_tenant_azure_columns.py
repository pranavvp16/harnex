"""Remove legacy Tenant Azure Search / blob columns (unused after pgvector).

Revision ID: 20260511_0005
Revises: 20260511_0004
Create Date: 2026-05-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260511_0005"
down_revision: str | None = "20260511_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("tenants", "azure_search_index")
    op.drop_column("tenants", "azure_blob_container")


def downgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("azure_search_index", sa.String(128), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column("azure_blob_container", sa.String(128), nullable=True),
    )
