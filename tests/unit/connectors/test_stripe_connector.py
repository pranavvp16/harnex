from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from harnex_api.connectors.base import ConnectionConfig, ConnectorTestEndpoint, LoadedSpec
from harnex_api.connectors.stripe import STRIPE_OPENAPI_URL, StripeConnector
from harnex_api.db.models import AuthFlow, ConnectionMode


@pytest.fixture
def connector() -> StripeConnector:
    return StripeConnector()


@pytest.fixture
def bare_connection() -> ConnectionConfig:
    return ConnectionConfig(
        id="conn-1",
        tenant_id="tenant-1",
        connector_key="stripe",
        mode=ConnectionMode.builtin,
        name="My Stripe",
        base_url=None,
        spec_url=None,
        spec_blob_path=None,
        auth_flow=AuthFlow.bearer,
        auth_config={},
    )


class TestStripeConnectorMetadata:
    def test_key(self, connector: StripeConnector) -> None:
        assert connector.key == "stripe"

    def test_display_name(self, connector: StripeConnector) -> None:
        assert connector.display_name == "Stripe"

    def test_supported_auth(self, connector: StripeConnector) -> None:
        assert connector.supported_auth == [AuthFlow.bearer]

    def test_default_base_url(self, connector: StripeConnector) -> None:
        assert connector.default_base_url == "https://api.stripe.com"

    def test_test_endpoint(self, connector: StripeConnector) -> None:
        assert connector.test_endpoint == ConnectorTestEndpoint(
            method="GET", path="/v1/account"
        )


class TestStripeConnectorLoadSpec:
    @patch(
        "harnex_api.services.ingestion.fetcher.fetch_spec_from_url",
        new_callable=AsyncMock,
    )
    async def test_load_spec_uses_default_url(
        self,
        mock_fetch: AsyncMock,
        connector: StripeConnector,
        bare_connection: ConnectionConfig,
    ) -> None:
        mock_fetch.return_value = LoadedSpec(
            document={"openapi": "3.0.0", "info": {"title": "Stripe API"}},
            source="url",
            raw_hash="abc123",
            original_format="openapi-3",
        )

        result = await connector.load_spec(bare_connection)

        mock_fetch.assert_awaited_once_with(STRIPE_OPENAPI_URL)
        assert result is not None
        assert result.source == "url"

    @patch(
        "harnex_api.services.ingestion.fetcher.fetch_spec_from_url",
        new_callable=AsyncMock,
    )
    async def test_load_spec_uses_custom_url(
        self,
        mock_fetch: AsyncMock,
        connector: StripeConnector,
        bare_connection: ConnectionConfig,
    ) -> None:
        custom_url = "https://example.com/custom-spec.json"
        connection = ConnectionConfig(
            **{**bare_connection.__dict__, "spec_url": custom_url}
        )
        mock_fetch.return_value = LoadedSpec(
            document={"openapi": "3.0.0", "info": {"title": "Custom Stripe"}},
            source="url",
            raw_hash="def456",
            original_format="openapi-3",
        )

        result = await connector.load_spec(connection)

        mock_fetch.assert_awaited_once_with(custom_url)
        assert result is not None

    @patch(
        "harnex_api.services.ingestion.fetcher.fetch_spec_from_url",
        new_callable=AsyncMock,
    )
    async def test_load_spec_propagates_fetch_error(
        self,
        mock_fetch: AsyncMock,
        connector: StripeConnector,
        bare_connection: ConnectionConfig,
    ) -> None:
        from harnex_api.services.ingestion.fetcher import SpecFetchError

        mock_fetch.side_effect = SpecFetchError("network error")

        with pytest.raises(SpecFetchError):
            await connector.load_spec(bare_connection)


class TestStripeConnectorInferBaseUrl:
    async def test_returns_default_when_no_base_url(
        self, connector: StripeConnector, bare_connection: ConnectionConfig
    ) -> None:
        url = await connector.infer_base_url(bare_connection, None)

        assert url == "https://api.stripe.com"

    async def test_uses_connection_base_url(
        self, connector: StripeConnector, bare_connection: ConnectionConfig
    ) -> None:
        connection = ConnectionConfig(
            **{**bare_connection.__dict__, "base_url": "https://custom.stripe.com"}
        )

        url = await connector.infer_base_url(connection, None)

        assert url == "https://custom.stripe.com"
