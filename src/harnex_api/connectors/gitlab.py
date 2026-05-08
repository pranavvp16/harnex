from __future__ import annotations

from typing import ClassVar

from harnex_api.connectors.base import (
    BaseConnector,
    ConnectionConfig,
    ConnectorTestEndpoint,
    LoadedSpec,
)
from harnex_api.db.models import AuthFlow

# GitLab publishes its REST API v4 OpenAPI 3 spec in the main repo.
GITLAB_OPENAPI_URL = (
    "https://gitlab.com/gitlab-org/gitlab/-/raw/master/doc/api/openapi/openapi.yaml"
)


class GitLabConnector(BaseConnector):
    """GitLab connector — supports both GitLab.com and self-hosted instances.

    For self-hosted, set connection.base_url to the instance root
    (e.g. https://gitlab.mycompany.com).  PRIVATE-TOKEN header auth maps to
    api_key_header with header_name='PRIVATE-TOKEN'.  Personal access tokens
    and OAuth 2.0 (authcode) are both supported.
    """

    key: ClassVar[str] = "gitlab"
    display_name: ClassVar[str] = "GitLab"
    supported_auth: ClassVar[list[AuthFlow]] = [
        AuthFlow.bearer,
        AuthFlow.oauth_authcode,
        AuthFlow.api_key_header,  # PRIVATE-TOKEN header
    ]
    default_base_url: ClassVar[str | None] = "https://gitlab.com"
    test_endpoint: ClassVar[ConnectorTestEndpoint] = ConnectorTestEndpoint(
        method="GET", path="/api/v4/user"
    )

    async def load_spec(self, connection: ConnectionConfig) -> LoadedSpec | None:
        from harnex_api.services.ingestion.fetcher import fetch_spec_from_url

        spec_url = connection.spec_url or GITLAB_OPENAPI_URL
        return await fetch_spec_from_url(spec_url)

    async def infer_base_url(
        self, connection: ConnectionConfig, spec: LoadedSpec | None
    ) -> str | None:
        # Self-hosted instances must supply base_url; fall back to .com.
        return connection.base_url or self.default_base_url


__all__ = ["GITLAB_OPENAPI_URL", "GitLabConnector"]
