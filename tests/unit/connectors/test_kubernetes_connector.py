from __future__ import annotations

import pytest

from harnex_api.connectors.base import LoadedSpec
from harnex_api.connectors.kubernetes import KubernetesConnector
from harnex_api.db.models import AuthFlow

from .conftest import make_connection, make_request


@pytest.fixture
def connector() -> KubernetesConnector:
    return KubernetesConnector()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_key() -> None:
    assert KubernetesConnector.key == "kubernetes"


def test_display_name() -> None:
    assert KubernetesConnector.display_name == "Kubernetes"


def test_supported_auth_bearer_and_basic() -> None:
    assert AuthFlow.bearer in KubernetesConnector.supported_auth
    assert AuthFlow.basic in KubernetesConnector.supported_auth


def test_default_base_url_is_none() -> None:
    # Kubernetes is always cluster-specific — no shared default URL.
    assert KubernetesConnector.default_base_url is None


def test_test_endpoint() -> None:
    ep = KubernetesConnector.test_endpoint
    assert ep.method == "GET"
    assert ep.path == "/api"


# ---------------------------------------------------------------------------
# infer_base_url — always returns connection.base_url, ignores spec servers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_infer_base_url_returns_connection_base_url(
    connector: KubernetesConnector,
) -> None:
    conn = make_connection(connector_key="kubernetes", base_url="https://k8s.example.com:6443")
    result = await connector.infer_base_url(conn, spec=None)
    assert result == "https://k8s.example.com:6443"


@pytest.mark.asyncio
async def test_infer_base_url_returns_none_when_not_set(
    connector: KubernetesConnector,
) -> None:
    conn = make_connection(connector_key="kubernetes", base_url=None)
    result = await connector.infer_base_url(conn, spec=None)
    assert result is None


@pytest.mark.asyncio
async def test_infer_base_url_ignores_spec_servers(
    connector: KubernetesConnector,
) -> None:
    # Kubernetes always returns connection.base_url directly — no spec server fallback.
    conn = make_connection(connector_key="kubernetes", base_url=None)
    spec = LoadedSpec(
        document={"servers": [{"url": "https://spec-cluster.example.com"}]},
        source="url",
        raw_hash="abc",
        original_format="openapi-3",
    )
    result = await connector.infer_base_url(conn, spec=spec)
    assert result is None


@pytest.mark.asyncio
async def test_infer_base_url_connection_url_wins_over_spec(
    connector: KubernetesConnector,
) -> None:
    conn = make_connection(connector_key="kubernetes", base_url="https://k8s.example.com:6443")
    spec = LoadedSpec(
        document={"servers": [{"url": "https://other-cluster.example.com"}]},
        source="url",
        raw_hash="abc",
        original_format="openapi-3",
    )
    result = await connector.infer_base_url(conn, spec=spec)
    assert result == "https://k8s.example.com:6443"


# ---------------------------------------------------------------------------
# before_execute — adds Accept: application/json header
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_before_execute_adds_accept_json_header(
    connector: KubernetesConnector,
) -> None:
    req = make_request(method="GET", path="/api/v1/pods", headers={})
    result = await connector.before_execute(req)
    assert result.headers.get("Accept") == "application/json"


@pytest.mark.asyncio
async def test_before_execute_caller_accept_overrides_default(
    connector: KubernetesConnector,
) -> None:
    # {"Accept": "application/json", **request.headers} — caller's value wins
    req = make_request(
        method="GET",
        path="/api/v1/pods",
        headers={"Accept": "application/yaml"},
    )
    result = await connector.before_execute(req)
    assert result.headers["Accept"] == "application/yaml"


@pytest.mark.asyncio
async def test_before_execute_preserves_method_and_path(
    connector: KubernetesConnector,
) -> None:
    req = make_request(method="DELETE", path="/api/v1/namespaces/default/pods/my-pod")
    result = await connector.before_execute(req)
    assert result.method == "DELETE"
    assert result.path == "/api/v1/namespaces/default/pods/my-pod"


@pytest.mark.asyncio
async def test_before_execute_preserves_body_and_query(
    connector: KubernetesConnector,
) -> None:
    req = make_request(
        method="POST",
        path="/api/v1/namespaces/default/pods",
        body={"apiVersion": "v1"},
        query={"dryRun": "All"},
    )
    result = await connector.before_execute(req)
    assert result.body == {"apiVersion": "v1"}
    assert result.query == {"dryRun": "All"}


@pytest.mark.asyncio
async def test_before_execute_returns_new_object(connector: KubernetesConnector) -> None:
    req = make_request(method="GET", path="/api")
    result = await connector.before_execute(req)
    assert result is not req
