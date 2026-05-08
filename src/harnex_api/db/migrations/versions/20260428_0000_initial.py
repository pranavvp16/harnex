"""initial schema

Revision ID: 20260428_0000
Revises:
Create Date: 2026-04-28
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260428_0000"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    tenant_plan = sa.Enum("free", "starter", "pro", "enterprise", name="tenant_plan")
    tenant_role = sa.Enum("owner", "admin", "developer", "viewer", name="tenant_role")
    connection_mode = sa.Enum(
        "builtin", "openapi_url", "openapi_upload", "bare_url", name="connection_mode"
    )
    connection_status = sa.Enum(
        "pending", "indexing", "ready", "error", "disabled", name="connection_status"
    )
    auth_flow = sa.Enum(
        "none",
        "api_key_header",
        "api_key_query",
        "bearer",
        "basic",
        "oauth_authcode",
        "oauth_clientcred",
        name="auth_flow",
    )
    execution_mode = sa.Enum("code", "structured", name="execution_mode")
    execution_status = sa.Enum("pending", "success", "error", "timeout", name="execution_status")

    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("plan", tenant_plan, nullable=False, server_default="free"),
        sa.Column("keycloak_org_id", sa.String(128)),
        sa.Column("infisical_project_id", sa.String(128)),
        sa.Column("azure_search_index", sa.String(128)),
        sa.Column("azure_blob_container", sa.String(128)),
        sa.Column("monthly_execution_quota", sa.BigInteger, nullable=False, server_default="10000"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"])

    op.create_table(
        "tenant_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("keycloak_user_id", sa.String(128), nullable=False),
        sa.Column("email", sa.String(320)),
        sa.Column("role", tenant_role, nullable=False, server_default="developer"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "keycloak_user_id", name="uq_membership_tenant_user"),
    )
    op.create_index("ix_tenant_memberships_tenant_id", "tenant_memberships", ["tenant_id"])
    op.create_index(
        "ix_tenant_memberships_keycloak_user_id", "tenant_memberships", ["keycloak_user_id"]
    )

    op.create_table(
        "connectors",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("is_builtin", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("default_base_url", sa.String(512)),
        sa.Column(
            "supported_auth",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("connector_key", sa.String(64), sa.ForeignKey("connectors.key")),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("mode", connection_mode, nullable=False),
        sa.Column("status", connection_status, nullable=False, server_default="pending"),
        sa.Column("base_url", sa.String(512)),
        sa.Column("spec_url", sa.String(2048)),
        sa.Column("spec_blob_path", sa.String(512)),
        sa.Column("spec_hash", sa.String(128)),
        sa.Column("auth_flow", auth_flow, nullable=False),
        sa.Column(
            "auth_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("endpoint_count", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_connection_tenant_status", "connections", ["tenant_id", "status"])

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("key_prefix", sa.String(16), nullable=False),
        sa.Column("key_hash", sa.String(256), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.String(128)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_api_key_tenant_active", "api_keys", ["tenant_id", "is_active"])
    op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"])

    op.create_table(
        "executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "connection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("connections.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "api_key_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("api_keys.id", ondelete="SET NULL"),
        ),
        sa.Column("mode", execution_mode, nullable=False),
        sa.Column("status", execution_status, nullable=False, server_default="pending"),
        sa.Column("operation_id", sa.String(256)),
        sa.Column("method", sa.String(16)),
        sa.Column("path", sa.String(1024)),
        sa.Column(
            "request_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "response_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("error_kind", sa.String(64)),
        sa.Column("error_message", sa.Text()),
        sa.Column("duration_ms", sa.BigInteger),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_execution_tenant_created", "executions", ["tenant_id", "created_at"])

    op.create_table(
        "usage_monthly",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("year_month", sa.String(7), nullable=False),
        sa.Column("executions", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("searches", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("embedding_tokens", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "year_month", name="uq_usage_tenant_month"),
    )

    op.create_table(
        "oauth_state",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("state", sa.String(128), nullable=False, unique=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "connection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("connections.id", ondelete="CASCADE"),
        ),
        sa.Column("connector_key", sa.String(64), nullable=False),
        sa.Column("code_verifier", sa.String(256)),
        sa.Column("redirect_uri", sa.String(1024), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_oauth_state_state", "oauth_state", ["state"])


def downgrade() -> None:
    op.drop_table("oauth_state")
    op.drop_table("usage_monthly")
    op.drop_table("executions")
    op.drop_table("api_keys")
    op.drop_table("connections")
    op.drop_table("connectors")
    op.drop_table("tenant_memberships")
    op.drop_table("tenants")
    for enum_name in (
        "execution_status",
        "execution_mode",
        "auth_flow",
        "connection_status",
        "connection_mode",
        "tenant_role",
        "tenant_plan",
    ):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
