from __future__ import annotations

from typing import ClassVar

from harnex_api.connectors.base import (
    BaseConnector,
    ConnectionConfig,
    ConnectorTestEndpoint,
    LoadedSpec,
)
from harnex_api.db.models import AuthFlow

# GitHub publishes a curated OpenAPI 3 description here. The production refresher
# can pin to a tag — for now we follow the latest descriptions.
GITHUB_OPENAPI_URL = (
    "https://raw.githubusercontent.com/github/rest-api-description/main/"
    "descriptions/api.github.com/api.github.com.json"
)


class GitHubConnector(BaseConnector):
    key: ClassVar[str] = "github"
    display_name: ClassVar[str] = "GitHub"
    supported_auth: ClassVar[list[AuthFlow]] = [AuthFlow.bearer, AuthFlow.oauth_authcode]
    default_base_url: ClassVar[str | None] = "https://api.github.com"
    test_endpoint: ClassVar[ConnectorTestEndpoint] = ConnectorTestEndpoint(
        method="GET", path="/user"
    )

    async def load_spec(self, connection: ConnectionConfig) -> LoadedSpec | None:
        from harnex_api.services.ingestion.fetcher import fetch_spec_from_url

        spec_url = connection.spec_url or GITHUB_OPENAPI_URL
        return await fetch_spec_from_url(spec_url)


__all__ = ["GITHUB_OPENAPI_URL", "GitHubConnector"]
