from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from harnex_api.config import get_settings
from harnex_api.db.session import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class TenantPlan(enum.StrEnum):
    free = "free"
    starter = "starter"
    pro = "pro"
    enterprise = "enterprise"


class TenantRole(enum.StrEnum):
    owner = "owner"
    admin = "admin"
    developer = "developer"
    viewer = "viewer"


class ConnectionStatus(enum.StrEnum):
    pending = "pending"
    indexing = "indexing"
    ready = "ready"
    error = "error"
    disabled = "disabled"


class ConnectionMode(enum.StrEnum):
    builtin = "builtin"
    openapi_url = "openapi_url"
    openapi_upload = "openapi_upload"
    bare_url = "bare_url"


class AuthFlow(enum.StrEnum):
    none = "none"
    api_key_header = "api_key_header"
    api_key_query = "api_key_query"
    bearer = "bearer"
    basic = "basic"
    oauth_authcode = "oauth_authcode"
    oauth_clientcred = "oauth_clientcred"


class ExecutionStatus(enum.StrEnum):
    pending = "pending"
    success = "success"
    error = "error"
    timeout = "timeout"


class ExecutionMode(enum.StrEnum):
    code = "code"
    structured = "structured"


class SpecSourceType(enum.StrEnum):
    builtin = "builtin"
    openapi_url = "openapi_url"
    openapi_upload = "openapi_upload"
    bare_url = "bare_url"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    plan: Mapped[TenantPlan] = mapped_column(
        Enum(TenantPlan, name="tenant_plan"), default=TenantPlan.free, nullable=False
    )
    keycloak_org_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    infisical_project_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    monthly_execution_quota: Mapped[int] = mapped_column(BigInteger, default=10_000, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    memberships: Mapped[list[TenantMembership]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    connections: Mapped[list[Connection]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    api_keys: Mapped[list[ApiKey]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )


class TenantMembership(Base, TimestampMixin):
    __tablename__ = "tenant_memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "keycloak_user_id", name="uq_membership_tenant_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    keycloak_user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    role: Mapped[TenantRole] = mapped_column(
        Enum(TenantRole, name="tenant_role"), default=TenantRole.developer, nullable=False
    )

    tenant: Mapped[Tenant] = relationship(back_populates="memberships")


class Connector(Base, TimestampMixin):
    """Catalog of available connectors (built-in + future plugin)."""

    __tablename__ = "connectors"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    supported_auth: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, nullable=False)


class Connection(Base, TimestampMixin):
    """A tenant's configured instance of a connector or generic API."""

    __tablename__ = "connections"
    __table_args__ = (Index("ix_connection_tenant_status", "tenant_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    connector_key: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("connectors.key"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    mode: Mapped[ConnectionMode] = mapped_column(Enum(ConnectionMode, name="connection_mode"))
    status: Mapped[ConnectionStatus] = mapped_column(
        Enum(ConnectionStatus, name="connection_status"),
        default=ConnectionStatus.pending,
        nullable=False,
    )
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    spec_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    spec_blob_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    spec_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    spec_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    spec_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("connector_specs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    auth_flow: Mapped[AuthFlow] = mapped_column(Enum(AuthFlow, name="auth_flow"))
    auth_config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    endpoint_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="connections")
    spec: Mapped[ConnectorSpec | None] = relationship()
    executions: Mapped[list[Execution]] = relationship(
        back_populates="connection", cascade="all, delete-orphan"
    )


class ConnectorSpec(Base, TimestampMixin):
    """Cross-tenant catalog of indexed OpenAPI specs.

    Keyed on `(source_type, source_key, spec_hash, embedding_model, embedding_dim)`
    so identical specs share one row per embedding space. Switching models or
    dimensions creates a new catalog row (same spec hash, different vectors)
    without colliding on the unique key. When upstream changes, `spec_hash`
    differs; the old row is GC'd once no connection points at it.
    """

    __tablename__ = "connector_specs"
    __table_args__ = (
        UniqueConstraint(
            "source_type",
            "source_key",
            "spec_hash",
            "embedding_model",
            "embedding_dim",
            name="uq_connector_specs_identity",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    source_type: Mapped[SpecSourceType] = mapped_column(
        Enum(SpecSourceType, name="spec_source_type"), nullable=False
    )
    source_key: Mapped[str] = mapped_column(String(2048), nullable=False)
    spec_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_dim: Mapped[int] = mapped_column(Integer, nullable=False)
    operation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_spec: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    chunks: Mapped[list[OperationChunk]] = relationship(
        back_populates="spec", cascade="all, delete-orphan", passive_deletes=True
    )


class OperationChunk(Base):
    """One row per OpenAPI operation, keyed on the spec catalog (not tenant).

    Each row carries the embedding vector and a generated tsvector for hybrid
    semantic + keyword search. Tenant scoping happens at query time via the
    JOIN through `connections.spec_id`, so multiple tenants can share these
    rows without leakage.
    """

    __tablename__ = "operation_chunks"
    __table_args__ = (
        Index("ix_operation_chunks_spec", "spec_id"),
        # vector + tsvector indexes are added in the alembic migration since
        # SQLAlchemy doesn't have a clean way to express HNSW + GIN parameters.
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    spec_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("connector_specs.id", ondelete="CASCADE"),
        nullable=False,
    )
    operation_id: Mapped[str] = mapped_column(String(256), nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(String(2048), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    semantic_tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    auth_scheme_keys: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    parameters: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    request_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    responses: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    embedding_text: Mapped[str] = mapped_column(Text, nullable=False)
    schema_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(get_settings().openai_embedding_dim), nullable=False
    )
    # `search_tsv tsvector GENERATED ALWAYS AS (...) STORED` lives in the DB
    # only — the migration creates it. Postgres rejects any INSERT/UPDATE that
    # specifies a value for a generated column, so we deliberately don't map
    # it on the ORM. Hybrid search reads it directly via raw SQL in
    # `services/search/vector_search.py`.

    spec: Mapped[ConnectorSpec] = relationship(back_populates="chunks")


class Execution(Base, TimestampMixin):
    __tablename__ = "executions"
    __table_args__ = (Index("ix_execution_tenant_created", "tenant_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("connections.id", ondelete="SET NULL"), nullable=True
    )
    api_key_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True
    )
    mode: Mapped[ExecutionMode] = mapped_column(Enum(ExecutionMode, name="execution_mode"))
    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus, name="execution_status"),
        default=ExecutionStatus.pending,
        nullable=False,
    )
    operation_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    method: Mapped[str | None] = mapped_column(String(16), nullable=True)
    path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    request_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    response_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    error_kind: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    connection: Mapped[Connection | None] = relationship(back_populates="executions")


class UsageMonthly(Base, TimestampMixin):
    __tablename__ = "usage_monthly"
    __table_args__ = (UniqueConstraint("tenant_id", "year_month", name="uq_usage_tenant_month"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    year_month: Mapped[str] = mapped_column(String(7), nullable=False)  # 'YYYY-MM'
    executions: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    searches: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    embedding_tokens: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)


class ApiKey(Base, TimestampMixin):
    """Tenant-scoped M2M keys for the MCP/REST surface.

    Optional `expires_at` lets callers issue time-limited keys; expiry is
    enforced at `authenticate_key()` time so revocation does not require
    a separate background job.

    `scope` describes which connections the key may execute against:
        {"type": "all"}  -> all tenant connections (default).
        {"type": "connections", "connection_ids": [uuid, ...]} -> restricted.
    """

    __tablename__ = "api_keys"
    __table_args__ = (Index("ix_api_key_tenant_active", "tenant_id", "is_active"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scope: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=lambda: {"type": "all"}, nullable=False
    )
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="api_keys")


class OAuthState(Base, TimestampMixin):
    """Short-lived OAuth state for auth-code flows; deleted after callback."""

    __tablename__ = "oauth_state"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    state: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("connections.id", ondelete="CASCADE"), nullable=True
    )
    connector_key: Mapped[str] = mapped_column(String(64), nullable=False)
    code_verifier: Mapped[str | None] = mapped_column(String(256), nullable=True)
    redirect_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


__all__ = [
    "JSON",
    "ApiKey",
    "AuthFlow",
    "Connection",
    "ConnectionMode",
    "ConnectionStatus",
    "Connector",
    "ConnectorSpec",
    "Execution",
    "ExecutionMode",
    "ExecutionStatus",
    "OAuthState",
    "OperationChunk",
    "SpecSourceType",
    "Tenant",
    "TenantMembership",
    "TenantPlan",
    "TenantRole",
    "UsageMonthly",
]
