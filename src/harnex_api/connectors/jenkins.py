from __future__ import annotations

from typing import ClassVar

from harnex_api.connectors.base import (
    BaseConnector,
    ConnectionConfig,
    ConnectorTestEndpoint,
    LoadedSpec,
)
from harnex_api.db.models import AuthFlow


class JenkinsConnector(BaseConnector):
    """Jenkins is self-hosted and varies by auth setup, so default to API token /
    basic auth. Spec source must be supplied per connection (curated seed spec
    or a Jenkins-published OpenAPI doc behind the user's URL).
    """

    key: ClassVar[str] = "jenkins"
    display_name: ClassVar[str] = "Jenkins"
    supported_auth: ClassVar[list[AuthFlow]] = [
        AuthFlow.basic,
        AuthFlow.bearer,
        AuthFlow.api_key_header,
    ]
    default_base_url: ClassVar[str | None] = None
    test_endpoint: ClassVar[ConnectorTestEndpoint] = ConnectorTestEndpoint(
        method="GET", path="/me/api/json"
    )

    async def load_spec(self, connection: ConnectionConfig) -> LoadedSpec | None:
        if not connection.spec_url and not connection.spec_blob_path:
            return None
        from harnex_api.services.ingestion.fetcher import fetch_spec_for_connection

        return await fetch_spec_for_connection(connection)


__all__ = ["JenkinsConnector"]
