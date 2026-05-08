from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    azure_search_index: Mapped[str | None] = mapped_column(String(128), nullable=True)
    azure_blob_container: Mapped[str | None] = mapped_column(String(128), nullable=True)
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
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)


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
    spec_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    auth_flow: Mapped[AuthFlow] = mapped_column(Enum(AuthFlow, name="auth_flow"))
    auth_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    endpoint_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="connections")
    executions: Mapped[list[Execution]] = relationship(
        back_populates="connection", cascade="all, delete-orphan"
    )


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
    request_summary: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    response_summary: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
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
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


__all__ = [
    "JSON",
    "ApiKey",
    "AuthFlow",
    "Connection",
    "ConnectionMode",
    "ConnectionStatus",
    "Connector",
    "Execution",
    "ExecutionMode",
    "ExecutionStatus",
    "OAuthState",
    "Tenant",
    "TenantMembership",
    "TenantPlan",
    "TenantRole",
    "UsageMonthly",
]
