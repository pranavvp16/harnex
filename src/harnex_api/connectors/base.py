from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar, Protocol, runtime_checkable

from harnex_api.db.models import AuthFlow, ConnectionMode


@dataclass(frozen=True)
class ConnectionConfig:
    """Immutable snapshot of one tenant connection passed into connector operations."""

    id: str
    tenant_id: str
    connector_key: str | None
    mode: ConnectionMode
    name: str
    base_url: str | None
    spec_url: str | None
    spec_blob_path: str | None
    auth_flow: AuthFlow
    auth_config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LoadedSpec:
    """A normalized OpenAPI 3.x document with metadata about how it was loaded."""

    document: dict[str, Any]
    source: str  # 'url' | 'upload' | 'builtin' | 'inline'
    raw_hash: str
    original_format: str  # 'openapi-3' | 'swagger-2' | 'unknown'


@dataclass(frozen=True)
class ExecuteRequest:
    """Structured representation of an outbound request — code-mode generates one of these."""

    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    query: dict[str, str] = field(default_factory=dict)
    body: Any | None = None
    operation_id: str | None = None


@runtime_checkable
class Connector(Protocol):
    """Contract for built-in and user-supplied connectors.

    All flows (built-in connector, OpenAPI URL/upload, bare API URL, future plugin)
    route through this Protocol so that ingestion, search, auth, and execute
    treat them uniformly.
    """

    key: str
    display_name: str
    supported_auth: list[AuthFlow]
    default_base_url: str | None

    async def load_spec(self, connection: ConnectionConfig) -> LoadedSpec | None:
        """Return a normalized OpenAPI 3.x document, or None if there is no spec."""
        ...

    async def infer_base_url(
        self, connection: ConnectionConfig, spec: LoadedSpec | None
    ) -> str | None:
        """Pick a base URL given the connection + parsed spec."""
        ...

    async def build_auth_context(
        self,
        tenant_id: str,
        connection_id: str,
        auth_flow: AuthFlow,
        auth_config: dict[str, Any],
    ) -> Any:
        """Resolve secrets from the vault and return an AuthContext for execution."""
        ...

    async def before_execute(self, request: ExecuteRequest) -> ExecuteRequest:
        """Optional last-mile transform before the request hits the sandbox."""
        ...


class BaseConnector:
    """Default Connector implementation — subclasses override what they need.

    `before_execute` defaults to identity; `build_auth_context` defers to the
    shared vault loader so most connectors only override `load_spec` and
    `infer_base_url`.
    """

    key: ClassVar[str] = ""
    display_name: ClassVar[str] = ""
    supported_auth: ClassVar[list[AuthFlow]] = []
    default_base_url: ClassVar[str | None] = None

    async def load_spec(self, connection: ConnectionConfig) -> LoadedSpec | None:
        return None

    async def infer_base_url(
        self, connection: ConnectionConfig, spec: LoadedSpec | None
    ) -> str | None:
        if connection.base_url:
            return connection.base_url
        if spec is not None:
            servers = spec.document.get("servers") or []
            if servers and isinstance(servers, list):
                first = servers[0]
                if isinstance(first, dict) and isinstance(first.get("url"), str):
                    return first["url"]
        return self.default_base_url

    async def build_auth_context(
        self,
        tenant_id: str,
        connection_id: str,
        auth_flow: AuthFlow,
        auth_config: dict[str, Any],
    ) -> Any:
        from harnex_api.auth.strategies import AuthCredentials, get_strategy
        from harnex_api.auth.vault import load_connection_credentials

        creds_values = await load_connection_credentials(
            tenant_id=tenant_id, connection_id=connection_id, auth_flow=auth_flow
        )
        return get_strategy(auth_flow).build(
            auth_config=auth_config,
            creds=AuthCredentials(flow=auth_flow, values=creds_values),
        )

    async def before_execute(self, request: ExecuteRequest) -> ExecuteRequest:
        return request


__all__ = [
    "BaseConnector",
    "ConnectionConfig",
    "Connector",
    "ExecuteRequest",
    "LoadedSpec",
]
