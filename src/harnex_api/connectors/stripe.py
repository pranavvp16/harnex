from __future__ import annotations

from typing import ClassVar

from harnex_api.connectors.base import (
    BaseConnector,
    ConnectionConfig,
    ConnectorTestEndpoint,
    LoadedSpec,
)
from harnex_api.db.models import AuthFlow

STRIPE_OPENAPI_URL = (
    "https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json"
)


class StripeConnector(BaseConnector):
    """Stripe payments API connector.

    Fixed base URL (api.stripe.com), bearer auth via Stripe API keys
    (sk_live_... or sk_test_...). Official OpenAPI spec loaded from
    https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json.
    """

    key: ClassVar[str] = "stripe"
    display_name: ClassVar[str] = "Stripe"
    supported_auth: ClassVar[list[AuthFlow]] = [AuthFlow.bearer]
    default_base_url: ClassVar[str | None] = "https://api.stripe.com"
    test_endpoint: ClassVar[ConnectorTestEndpoint] = ConnectorTestEndpoint(
        method="GET", path="/v1/account"
    )

    async def load_spec(self, connection: ConnectionConfig) -> LoadedSpec | None:
        from harnex_api.services.ingestion.fetcher import fetch_spec_from_url

        spec_url = connection.spec_url or STRIPE_OPENAPI_URL
        return await fetch_spec_from_url(spec_url)


__all__ = ["STRIPE_OPENAPI_URL", "StripeConnector"]
