from __future__ import annotations

from typing import ClassVar

from harnex_api.connectors.base import BaseConnector, ConnectionConfig, LoadedSpec
from harnex_api.db.models import AuthFlow


class GenericConnector(BaseConnector):
    """User-supplied connection: OpenAPI URL, uploaded spec, or bare API base URL.

    Spec loading delegates to the ingestion fetcher (which handles URL/upload/blob
    storage); this connector just composes inputs and applies sensible defaults.
    """

    key: ClassVar[str] = "generic"
    display_name: ClassVar[str] = "Generic API"
    supported_auth: ClassVar[list[AuthFlow]] = [
        AuthFlow.none,
        AuthFlow.api_key_header,
        AuthFlow.api_key_query,
        AuthFlow.bearer,
        AuthFlow.basic,
        AuthFlow.oauth_authcode,
        AuthFlow.oauth_clientcred,
    ]
    default_base_url: ClassVar[str | None] = None

    async def load_spec(self, connection: ConnectionConfig) -> LoadedSpec | None:
        from harnex_api.services.ingestion.fetcher import fetch_spec_for_connection

        return await fetch_spec_for_connection(connection)


__all__ = ["GenericConnector"]
