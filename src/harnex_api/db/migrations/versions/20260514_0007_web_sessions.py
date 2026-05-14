"""BFF console sessions — web_sessions table.

Backs the cookie-based auth for the web console. The browser only carries an
opaque session id (hashed into sid_hash); Keycloak tokens are stored Fernet-
encrypted server-side.

Revision ID: 20260514_0007
Revises: 20260512_0006
Create Date: 2026-05-14
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260514_0007"
down_revision: str | None = "20260512_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "web_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sid_hash", sa.LargeBinary(length=32), nullable=False),
        sa.Column("keycloak_user_id", sa.String(128), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("access_token_ct", sa.LargeBinary(), nullable=False),
        sa.Column("refresh_token_ct", sa.LargeBinary(), nullable=False),
        sa.Column("id_token_ct", sa.LargeBinary(), nullable=True),
        sa.Column(
            "claims_cache",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("csrf_token", sa.String(64), nullable=False),
        sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idle_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_seen_ip", sa.String(64), nullable=True),
        sa.Column("last_seen_ua", sa.String(256), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_web_sessions_sid_hash",
        "web_sessions",
        ["sid_hash"],
        unique=True,
    )
    op.create_index(
        "ix_web_sessions_keycloak_user_id",
        "web_sessions",
        ["keycloak_user_id"],
    )
    op.create_index(
        "ix_web_sessions_idle_expires_at",
        "web_sessions",
        ["idle_expires_at"],
    )
    op.create_index(
        "ix_web_sessions_absolute_expires_at",
        "web_sessions",
        ["absolute_expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_web_sessions_absolute_expires_at", table_name="web_sessions")
    op.drop_index("ix_web_sessions_idle_expires_at", table_name="web_sessions")
    op.drop_index("ix_web_sessions_keycloak_user_id", table_name="web_sessions")
    op.drop_index("ix_web_sessions_sid_hash", table_name="web_sessions")
    op.drop_table("web_sessions")
