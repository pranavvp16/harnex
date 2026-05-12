"""Unit tests for the code-mode execute path (execute_code).

Uses a FakeRunner injected via set_sandbox_runner so no Blaxel connectivity
is required. DB interactions are stubbed with AsyncMock.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from harnex_api.db.models import ExecutionMode, ExecutionStatus
from harnex_api.services.execute import sandbox as sbx
from harnex_api.services.execute import set_sandbox_runner
from harnex_api.services.execute.operation import ExecuteParams
from harnex_api.services.execute.runner import execute_code
from harnex_api.services.execute.sandbox import SandboxResult, generate_fetch_script

# ---------------------------------------------------------------------------
# Shared OpenAPI spec fixture
# ---------------------------------------------------------------------------

SPEC: dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "test", "version": "0"},
    "paths": {
        "/items/{item_id}": {
            "get": {
                "operationId": "get_item",
                "parameters": [
                    {
                        "name": "item_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {"200": {"description": "ok"}},
            }
        }
    },
}


# ---------------------------------------------------------------------------
# Fake sandbox runner
# ---------------------------------------------------------------------------


class ProgrammableFakeRunner:
    """Returns a caller-supplied SandboxResult on the next run_node_script call."""

    def __init__(self, result: SandboxResult) -> None:
        self._result = result
        self.calls: list[dict[str, Any]] = []

    async def run_command(
        self, *, command: str, working_dir: str | None = None, timeout_seconds: int | None = None
    ) -> SandboxResult:
        return SandboxResult(exit_code=0, stdout="", stderr="")

    async def run_node_script(
        self, *, source: str, timeout_seconds: int | None = None
    ) -> SandboxResult:
        self.calls.append({"source": source, "timeout": timeout_seconds})
        return self._result


# ---------------------------------------------------------------------------
# Helper: build a minimal fake DB session + connection mock
# ---------------------------------------------------------------------------


def _make_session_with_connection(
    connector_key: str = "generic",
    base_url: str = "https://api.example.com",
    spec_document: dict[str, Any] | None = None,
) -> AsyncMock:
    """Return an AsyncMock session whose get_connection returns a minimal connection."""
    conn = MagicMock()
    conn.id = uuid4()
    conn.tenant_id = uuid4()
    conn.connector_key = connector_key
    conn.mode = "openapi_url"
    conn.name = "test"
    conn.base_url = base_url
    conn.spec_url = None
    conn.spec_blob_path = None
    conn.auth_flow = "api_key_header"
    conn.auth_config = {"header_name": "X-Api-Key", "secret_name": "test-secret"}

    session = MagicMock()
    session.execute = AsyncMock()

    # Patch get_connection + resolve connector inline per test via monkeypatching.
    # We store the conn on session so tests can reference it.
    session._fake_conn = conn
    return session


def _magic_db_session() -> MagicMock:
    """MagicMock AsyncSession: ``execute`` is awaitable (usage_monthly upsert)."""
    s = MagicMock()
    s.execute = AsyncMock()
    return s


@pytest.fixture(autouse=True)
def patch_execute_usage_session_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    """execute_code records usage via ``session_scope``; stub it so unit tests skip Postgres."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def fake_scope() -> Any:
        yield _magic_db_session()

    monkeypatch.setattr(
        "harnex_api.services.execute.runner.session_scope",
        fake_scope,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_runner():
    """Restore global sandbox runner after each test."""
    yield
    sbx._runner = None  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# generate_fetch_script tests
# ---------------------------------------------------------------------------


def test_generate_fetch_script_basic_get() -> None:
    script = generate_fetch_script(
        method="GET",
        url="https://api.example.com/items/42",
        headers={"Authorization": "Bearer tok"},
        query={"page": "1"},
        body=None,
    )
    assert "https://api.example.com/items/42" in script
    assert '"GET"' in script
    assert '"Authorization"' in script
    assert '"Bearer tok"' in script
    assert '"page"' in script
    assert "_body = null" in script
    assert "console.log(JSON.stringify" in script


def test_generate_fetch_script_post_with_body() -> None:
    script = generate_fetch_script(
        method="POST",
        url="https://api.example.com/items",
        headers={},
        query={},
        body={"name": "widget", "price": 9.99},
    )
    assert '"POST"' in script
    assert '"name"' in script
    assert '"widget"' in script
    # body is not null — should set Content-Type if missing
    assert "Content-Type" in script
    assert "application/json" in script


def test_generate_fetch_script_embeds_values_as_json_literals() -> None:
    # Values that would break string interpolation must be JSON-safe
    tricky_headers = {"X-Key": 'value with "quotes" and \\backslash'}
    script = generate_fetch_script(
        method="GET",
        url="https://example.com/",
        headers=tricky_headers,
        query={},
        body=None,
    )
    # json.dumps round-trip: the header value must appear escaped in the script
    assert json.dumps(tricky_headers["X-Key"]) in script


# ---------------------------------------------------------------------------
# execute_code happy path
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_execute_code_success() -> None:
    sandbox_stdout = json.dumps(
        {"http_status": 200, "headers": {"content-type": "application/json"}, "body": {"id": "42"}}
    )
    fake_runner = ProgrammableFakeRunner(
        SandboxResult(exit_code=0, stdout=sandbox_stdout, stderr="")
    )
    set_sandbox_runner(fake_runner)

    tenant_id = uuid4()
    connection_id = uuid4()

    with (
        patch("harnex_api.services.execute.runner.get_connection") as mock_get_conn,
        patch("harnex_api.services.execute.runner._resolve_connector_and_spec") as mock_resolve,
    ):
        conn = MagicMock()
        conn.id = connection_id
        conn.tenant_id = tenant_id
        conn.connector_key = "generic"
        conn.auth_flow = "api_key_header"
        conn.auth_config = {}
        mock_get_conn.return_value = conn

        from harnex_api.auth.strategies import AuthContext
        from harnex_api.connectors.base import LoadedSpec
        from harnex_api.db.models import AuthFlow

        mock_connector = MagicMock()
        mock_connector.infer_base_url = AsyncMock(return_value="https://api.example.com")
        mock_connector.build_auth_context = AsyncMock(
            return_value=AuthContext(
                flow=AuthFlow.api_key_header, headers={"X-Api-Key": "secret"}, query={}
            )
        )
        mock_connector.before_execute = AsyncMock(side_effect=lambda req: req)

        mock_spec = MagicMock(spec=LoadedSpec)
        mock_spec.document = SPEC
        mock_resolve.return_value = (mock_connector, mock_spec)

        session = _magic_db_session()
        params = ExecuteParams(path={"item_id": "42"}, query={}, headers={}, body=None)

        outcome = await execute_code(
            session,
            tenant_id=tenant_id,
            connection_id=connection_id,
            operation_id="get_item",
            params=params,
        )

    assert outcome.status == ExecutionStatus.success
    assert outcome.http_status == 200
    assert outcome.response_body == {"id": "42"}
    assert outcome.error_kind is None
    assert len(fake_runner.calls) == 1
    # Verify the sandbox was called with a script containing the full URL
    assert "api.example.com/items/42" in fake_runner.calls[0]["source"]
    # Verify Execution row was written with mode=code
    session.add.assert_called_once()
    execution_row = session.add.call_args[0][0]
    assert execution_row.mode == ExecutionMode.code


@pytest.mark.anyio
async def test_execute_code_non_2xx_becomes_error_status() -> None:
    sandbox_stdout = json.dumps(
        {"http_status": 404, "headers": {}, "body": {"detail": "not found"}}
    )
    set_sandbox_runner(
        ProgrammableFakeRunner(SandboxResult(exit_code=0, stdout=sandbox_stdout, stderr=""))
    )

    tenant_id = uuid4()
    connection_id = uuid4()

    with (
        patch("harnex_api.services.execute.runner.get_connection") as mock_get_conn,
        patch("harnex_api.services.execute.runner._resolve_connector_and_spec") as mock_resolve,
    ):
        conn = MagicMock()
        conn.id = connection_id
        conn.tenant_id = tenant_id
        conn.connector_key = "generic"
        conn.auth_flow = "api_key_header"
        conn.auth_config = {}
        mock_get_conn.return_value = conn

        from harnex_api.auth.strategies import AuthContext
        from harnex_api.connectors.base import LoadedSpec
        from harnex_api.db.models import AuthFlow

        mock_connector = MagicMock()
        mock_connector.infer_base_url = AsyncMock(return_value="https://api.example.com")
        mock_connector.build_auth_context = AsyncMock(
            return_value=AuthContext(flow=AuthFlow.none, headers={}, query={})
        )
        mock_connector.before_execute = AsyncMock(side_effect=lambda req: req)

        mock_spec = MagicMock(spec=LoadedSpec)
        mock_spec.document = SPEC
        mock_resolve.return_value = (mock_connector, mock_spec)

        session = _magic_db_session()
        params = ExecuteParams(path={"item_id": "99"}, query={}, headers={}, body=None)

        outcome = await execute_code(
            session,
            tenant_id=tenant_id,
            connection_id=connection_id,
            operation_id="get_item",
            params=params,
        )

    assert outcome.status == ExecutionStatus.error
    assert outcome.http_status == 404
    assert outcome.error_kind == "http_404"


@pytest.mark.anyio
async def test_execute_code_sandbox_crash() -> None:
    set_sandbox_runner(
        ProgrammableFakeRunner(
            SandboxResult(exit_code=1, stdout="", stderr="TypeError: fetch is not defined")
        )
    )

    tenant_id = uuid4()
    connection_id = uuid4()

    with (
        patch("harnex_api.services.execute.runner.get_connection") as mock_get_conn,
        patch("harnex_api.services.execute.runner._resolve_connector_and_spec") as mock_resolve,
    ):
        conn = MagicMock()
        conn.id = connection_id
        conn.tenant_id = tenant_id
        conn.connector_key = "generic"
        conn.auth_flow = "api_key_header"
        conn.auth_config = {}
        mock_get_conn.return_value = conn

        from harnex_api.auth.strategies import AuthContext
        from harnex_api.connectors.base import LoadedSpec
        from harnex_api.db.models import AuthFlow

        mock_connector = MagicMock()
        mock_connector.infer_base_url = AsyncMock(return_value="https://api.example.com")
        mock_connector.build_auth_context = AsyncMock(
            return_value=AuthContext(flow=AuthFlow.none, headers={}, query={})
        )
        mock_connector.before_execute = AsyncMock(side_effect=lambda req: req)

        mock_spec = MagicMock(spec=LoadedSpec)
        mock_spec.document = SPEC
        mock_resolve.return_value = (mock_connector, mock_spec)

        session = _magic_db_session()
        params = ExecuteParams(path={"item_id": "1"}, query={}, headers={}, body=None)

        outcome = await execute_code(
            session,
            tenant_id=tenant_id,
            connection_id=connection_id,
            operation_id="get_item",
            params=params,
        )

    assert outcome.status == ExecutionStatus.error
    assert outcome.error_kind == "sandbox_error"
    assert "TypeError" in (outcome.error_message or "")


@pytest.mark.anyio
async def test_execute_code_invalid_json_stdout() -> None:
    set_sandbox_runner(
        ProgrammableFakeRunner(SandboxResult(exit_code=0, stdout="this is not json", stderr=""))
    )

    tenant_id = uuid4()
    connection_id = uuid4()

    with (
        patch("harnex_api.services.execute.runner.get_connection") as mock_get_conn,
        patch("harnex_api.services.execute.runner._resolve_connector_and_spec") as mock_resolve,
    ):
        conn = MagicMock()
        conn.id = connection_id
        conn.tenant_id = tenant_id
        conn.connector_key = "generic"
        conn.auth_flow = "api_key_header"
        conn.auth_config = {}
        mock_get_conn.return_value = conn

        from harnex_api.auth.strategies import AuthContext
        from harnex_api.connectors.base import LoadedSpec
        from harnex_api.db.models import AuthFlow

        mock_connector = MagicMock()
        mock_connector.infer_base_url = AsyncMock(return_value="https://api.example.com")
        mock_connector.build_auth_context = AsyncMock(
            return_value=AuthContext(flow=AuthFlow.none, headers={}, query={})
        )
        mock_connector.before_execute = AsyncMock(side_effect=lambda req: req)

        mock_spec = MagicMock(spec=LoadedSpec)
        mock_spec.document = SPEC
        mock_resolve.return_value = (mock_connector, mock_spec)

        session = _magic_db_session()
        params = ExecuteParams(path={"item_id": "1"}, query={}, headers={}, body=None)

        outcome = await execute_code(
            session,
            tenant_id=tenant_id,
            connection_id=connection_id,
            operation_id="get_item",
            params=params,
        )

    assert outcome.status == ExecutionStatus.error
    assert outcome.error_kind == "sandbox_output_invalid"


@pytest.mark.anyio
async def test_execute_code_operation_not_found() -> None:
    set_sandbox_runner(ProgrammableFakeRunner(SandboxResult(exit_code=0, stdout="", stderr="")))

    tenant_id = uuid4()
    connection_id = uuid4()

    with (
        patch("harnex_api.services.execute.runner.get_connection") as mock_get_conn,
        patch("harnex_api.services.execute.runner._resolve_connector_and_spec") as mock_resolve,
    ):
        conn = MagicMock()
        conn.id = connection_id
        conn.tenant_id = tenant_id
        conn.connector_key = "generic"
        conn.auth_flow = "api_key_header"
        conn.auth_config = {}
        mock_get_conn.return_value = conn

        from harnex_api.connectors.base import LoadedSpec

        mock_connector = MagicMock()
        mock_connector.infer_base_url = AsyncMock(return_value="https://api.example.com")

        mock_spec = MagicMock(spec=LoadedSpec)
        mock_spec.document = SPEC
        mock_resolve.return_value = (mock_connector, mock_spec)

        session = _magic_db_session()
        params = ExecuteParams(path={}, query={}, headers={}, body=None)

        outcome = await execute_code(
            session,
            tenant_id=tenant_id,
            connection_id=connection_id,
            operation_id="no_such_operation",
            params=params,
        )

    assert outcome.status == ExecutionStatus.error
    assert outcome.error_kind == "operation_not_found"
    # Sandbox should never have been invoked
    # (the FakeRunner's calls list is empty because _prepare_execute returned early)
