from __future__ import annotations

from typing import ClassVar

from harnex_api.connectors.base import (
    BaseConnector,
    ConnectionConfig,
    ExecuteRequest,
    LoadedSpec,
)
from harnex_api.db.models import AuthFlow


class LinearConnector(BaseConnector):
    """Linear connector.

    Linear exposes a GraphQL API only — no official OpenAPI spec exists.
    All requests route to POST /graphql; before_execute enforces this so that
    operation builders targeting any path are normalized to the single endpoint.

    Supply a community-curated OpenAPI spec via connection.spec_url if you want
    semantic search over Linear operations; without a spec the connector still
    executes raw GraphQL bodies passed through body.
    """

    key: ClassVar[str] = "linear"
    display_name: ClassVar[str] = "Linear"
    supported_auth: ClassVar[list[AuthFlow]] = [
        AuthFlow.bearer,
        AuthFlow.oauth_authcode,
    ]
    default_base_url: ClassVar[str | None] = "https://api.linear.app"

    async def load_spec(self, connection: ConnectionConfig) -> LoadedSpec | None:
        if not connection.spec_url:
            return None
        from harnex_api.services.ingestion.fetcher import fetch_spec_from_url

        return await fetch_spec_from_url(connection.spec_url)

    async def before_execute(self, request: ExecuteRequest) -> ExecuteRequest:
        # All Linear API calls are POST to /graphql regardless of OpenAPI path.
        headers = {**request.headers, "Content-Type": "application/json"}
        return ExecuteRequest(
            method="POST",
            path="/graphql",
            headers=headers,
            query=request.query,
            body=request.body,
            operation_id=request.operation_id,
        )


__all__ = ["LinearConnector"]
