from __future__ import annotations

from typing import Any

from harnex_api.connectors.base import ConnectionConfig, ExecuteRequest
from harnex_api.db.models import AuthFlow, ConnectionMode


def make_connection(
    connector_key: str = "generic",
    base_url: str | None = None,
    spec_url: str | None = None,
    auth_flow: AuthFlow = AuthFlow.bearer,
    **extra: Any,
) -> ConnectionConfig:
    """Minimal ConnectionConfig for connector unit tests."""
    return ConnectionConfig(
        id="conn-test-001",
        tenant_id="tenant-test-001",
        connector_key=connector_key,
        mode=ConnectionMode.builtin,
        name="Test Connection",
        base_url=base_url,
        spec_url=spec_url,
        spec_blob_path=None,
        auth_flow=auth_flow,
        auth_config={},
        spec_blob=None,
    )


def make_request(
    method: str = "GET",
    path: str = "/",
    headers: dict[str, str] | None = None,
    query: dict[str, str] | None = None,
    body: Any = None,
    operation_id: str | None = None,
) -> ExecuteRequest:
    """Minimal ExecuteRequest for before_execute tests."""
    return ExecuteRequest(
        method=method,
        path=path,
        headers=headers or {},
        query=query or {},
        body=body,
        operation_id=operation_id,
    )
