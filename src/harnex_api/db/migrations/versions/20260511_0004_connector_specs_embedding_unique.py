"""Include embedding model+dim in connector_specs uniqueness

Revision ID: 20260511_0004
Revises: 20260510_0003
Create Date: 2026-05-11
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260511_0004"
down_revision: str | None = "20260510_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("uq_connector_specs_identity", "connector_specs", type_="unique")
    op.create_unique_constraint(
        "uq_connector_specs_identity",
        "connector_specs",
        ["source_type", "source_key", "spec_hash", "embedding_model", "embedding_dim"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_connector_specs_identity", "connector_specs", type_="unique")
    op.create_unique_constraint(
        "uq_connector_specs_identity",
        "connector_specs",
        ["source_type", "source_key", "spec_hash"],
    )
