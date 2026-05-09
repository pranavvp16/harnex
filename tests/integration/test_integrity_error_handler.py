from __future__ import annotations

import httpx
import pytest
from sqlalchemy.exc import IntegrityError

from harnex_api.main import create_app


class _FakeOrigError(Exception):
    """Stand-in for an asyncpg constraint error."""

    def __init__(self, message: str, constraint_name: str | None = None) -> None:
        super().__init__(message)
        self.constraint_name = constraint_name


@pytest.fixture
def app_with_failing_route():
    app = create_app()

    @app.get("/_test/raise-integrity")
    async def raise_integrity() -> dict[str, str]:
        raise IntegrityError(
            statement="INSERT INTO things",
            params={},
            orig=_FakeOrigError(
                "duplicate key value violates unique constraint \"uq_things_name\"",
                constraint_name="uq_things_name",
            ),
        )

    @app.get("/_test/raise-integrity-no-constraint")
    async def raise_integrity_no_constraint() -> dict[str, str]:
        raise IntegrityError(
            statement="INSERT INTO things",
            params={},
            orig=_FakeOrigError("FK violation"),
        )

    return app


async def test_integrity_error_returns_structured_400(app_with_failing_route) -> None:
    transport = httpx.ASGITransport(app=app_with_failing_route)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/_test/raise-integrity")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "constraint_violation"
    assert body["constraint"] == "uq_things_name"
    # In local env we surface the underlying driver message.
    assert "duplicate key value" in body["message"]


async def test_integrity_error_without_constraint_name(app_with_failing_route) -> None:
    transport = httpx.ASGITransport(app=app_with_failing_route)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/_test/raise-integrity-no-constraint")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "constraint_violation"
    assert "constraint" not in body
