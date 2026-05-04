from __future__ import annotations

from typing import ClassVar

from harnex_api.connectors.base import (
    BaseConnector,
    ConnectionConfig,
    ExecuteRequest,
    LoadedSpec,
)
from harnex_api.db.models import AuthFlow


class KubernetesConnector(BaseConnector):
    """Kubernetes API connector.

    Targets the kube-apiserver REST API.  Base URL must be supplied via
    connection.base_url (e.g. https://k8s.mycompany.com:6443).

    Spec loading: set connection.spec_url to <base_url>/openapi/v2 to fetch the
    cluster's own spec (requires a valid bearer token at index time), or supply
    a pre-downloaded spec via upload.  No public static spec is bundled because
    the API surface varies by cluster version and installed CRDs.

    Auth: service-account JWT bearer tokens are the standard approach.
    Basic auth works for dev clusters; client-cert auth is not supported.
    """

    key: ClassVar[str] = "kubernetes"
    display_name: ClassVar[str] = "Kubernetes"
    supported_auth: ClassVar[list[AuthFlow]] = [
        AuthFlow.bearer,
        AuthFlow.basic,
    ]
    default_base_url: ClassVar[str | None] = None  # always cluster-specific

    async def load_spec(self, connection: ConnectionConfig) -> LoadedSpec | None:
        if not connection.spec_url and not connection.spec_blob_path:
            return None
        from harnex_api.services.ingestion.fetcher import fetch_spec_for_connection

        return await fetch_spec_for_connection(connection)

    async def infer_base_url(
        self, connection: ConnectionConfig, spec: LoadedSpec | None
    ) -> str | None:
        return connection.base_url

    async def before_execute(self, request: ExecuteRequest) -> ExecuteRequest:
        # Ensure JSON responses; kube-apiserver defaults vary by Accept header.
        headers = {"Accept": "application/json", **request.headers}
        return ExecuteRequest(
            method=request.method,
            path=request.path,
            headers=headers,
            query=request.query,
            body=request.body,
            operation_id=request.operation_id,
        )


__all__ = ["KubernetesConnector"]
