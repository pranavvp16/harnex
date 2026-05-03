from __future__ import annotations

from typing import ClassVar

from harnex_api.connectors.base import BaseConnector, ConnectionConfig, LoadedSpec
from harnex_api.db.models import AuthFlow

# Slack publishes an official OpenAPI v2 spec for the Web API.
SLACK_OPENAPI_URL = (
    "https://raw.githubusercontent.com/slackapi/slack-api-specs/master/"
    "web-api/slack_web_openapi_v2.json"
)


class SlackConnector(BaseConnector):
    """Slack Web API connector.

    Use bearer with a bot token (xoxb-...) for most agent use cases.
    oauth_authcode gives a user token (xoxp-...) for user-scoped actions.
    """

    key: ClassVar[str] = "slack"
    display_name: ClassVar[str] = "Slack"
    supported_auth: ClassVar[list[AuthFlow]] = [
        AuthFlow.bearer,
        AuthFlow.oauth_authcode,
    ]
    default_base_url: ClassVar[str | None] = "https://slack.com/api"

    async def load_spec(self, connection: ConnectionConfig) -> LoadedSpec | None:
        from harnex_api.services.ingestion.fetcher import fetch_spec_from_url

        spec_url = connection.spec_url or SLACK_OPENAPI_URL
        return await fetch_spec_from_url(spec_url)


__all__ = ["SLACK_OPENAPI_URL", "SlackConnector"]
