from __future__ import annotations

from typing import ClassVar

from harnex_api.connectors.base import BaseConnector, ConnectionConfig, LoadedSpec
from harnex_api.db.models import AuthFlow

# Atlassian publishes the Jira Cloud REST API v3 spec here.
JIRA_OPENAPI_URL = (
    "https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json"
)


class JiraConnector(BaseConnector):
    """Jira Cloud connector.

    Base URL is tenant-specific (https://<your-org>.atlassian.net) and must be
    supplied via connection.base_url.  Basic auth uses email + API token;
    OAuth 2.0 (3LO) grants scoped access via oauth_authcode.
    """

    key: ClassVar[str] = "jira"
    display_name: ClassVar[str] = "Jira"
    supported_auth: ClassVar[list[AuthFlow]] = [
        AuthFlow.oauth_authcode,
        AuthFlow.basic,
        AuthFlow.bearer,
    ]
    default_base_url: ClassVar[str | None] = None  # tenant-specific subdomain

    async def load_spec(self, connection: ConnectionConfig) -> LoadedSpec | None:
        from harnex_api.services.ingestion.fetcher import fetch_spec_from_url

        spec_url = connection.spec_url or JIRA_OPENAPI_URL
        return await fetch_spec_from_url(spec_url)

    async def infer_base_url(
        self, connection: ConnectionConfig, spec: LoadedSpec | None
    ) -> str | None:
        # Jira base URL is always org-specific; never fall through to spec servers.
        return connection.base_url


__all__ = ["JIRA_OPENAPI_URL", "JiraConnector"]
