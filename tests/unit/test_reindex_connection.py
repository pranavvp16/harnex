from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from harnex_api.db.models import (
    AuthFlow,
    Connection,
    ConnectionMode,
    ConnectionStatus,
)
from harnex_api.services.connections import reindex_connection
from harnex_api.services.ingestion.pipeline import IndexResult


@pytest.mark.asyncio
async def test_reindex_uses_persisted_spec_blob_without_connector_or_spec_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Upload-only rows store bytes on `spec_blob`; reindex must re-parse them."""
    tenant_id = uuid.uuid4()
    connection_id = uuid.uuid4()
    raw = (
        b'{"openapi":"3.0.3","info":{"title":"t","version":"1"},'
        b'"servers":[{"url":"https://example.com"}],'
        b'"paths":{"/x":{"get":{"summary":"hello","responses":{"200":{"description":"ok"}}}}}}'
    )
    conn = Connection(
        id=connection_id,
        tenant_id=tenant_id,
        connector_key=None,
        name="upload",
        mode=ConnectionMode.openapi_upload,
        status=ConnectionStatus.ready,
        spec_url=None,
        spec_blob=raw,
        auth_flow=AuthFlow.none,
    )

    session = MagicMock()
    monkeypatch.setattr(
        "harnex_api.services.connections.get_connection",
        AsyncMock(return_value=conn),
    )

    captured: dict[str, object] = {}

    async def fake_index_spec(
        *,
        session: object,
        connection: object,
        spec: object,
        embeddings: object | None = None,
    ) -> IndexResult:
        captured["spec"] = spec
        assert spec.source == "upload"
        return IndexResult(operation_count=1, chunk_count=1, spec_hash=spec.raw_hash)

    monkeypatch.setattr("harnex_api.services.connections.index_spec", fake_index_spec)

    result = await reindex_connection(session, tenant_id=tenant_id, connection_id=connection_id)
    assert result is not None
    assert result.operation_count == 1
    assert "spec" in captured
