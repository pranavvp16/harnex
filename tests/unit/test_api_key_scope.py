from __future__ import annotations

from uuid import UUID, uuid4

from harnex_api.services.api_key_auth import ApiKeyAuth, _scope_tuple


def test_scope_tuple_defaults_to_all_for_none() -> None:
    stype, ids = _scope_tuple(None)
    assert stype == "all"
    assert ids == ()


def test_scope_tuple_defaults_to_all_for_empty_dict() -> None:
    stype, ids = _scope_tuple({})
    assert stype == "all"
    assert ids == ()


def test_scope_tuple_parses_connection_ids() -> None:
    a, b = uuid4(), uuid4()
    stype, ids = _scope_tuple({"type": "connections", "connection_ids": [str(a), str(b)]})
    assert stype == "connections"
    assert ids == (a, b)


def test_scope_tuple_drops_invalid_ids() -> None:
    real = uuid4()
    stype, ids = _scope_tuple({"type": "connections", "connection_ids": [str(real), "not-a-uuid"]})
    assert stype == "connections"
    assert ids == (real,)


def test_allows_connection_for_all_scope() -> None:
    auth = ApiKeyAuth(api_key_id=uuid4(), tenant_id=uuid4())
    assert auth.allows_connection(uuid4()) is True


def test_allows_connection_for_restricted_scope() -> None:
    allowed = uuid4()
    forbidden = uuid4()
    auth = ApiKeyAuth(
        api_key_id=uuid4(),
        tenant_id=uuid4(),
        scope_type="connections",
        scope_connection_ids=(allowed,),
    )
    assert auth.allows_connection(allowed) is True
    assert auth.allows_connection(forbidden) is False


def test_allows_connection_handles_uuid_equality() -> None:
    cid = UUID("12345678-1234-5678-1234-567812345678")
    auth = ApiKeyAuth(
        api_key_id=uuid4(),
        tenant_id=uuid4(),
        scope_type="connections",
        scope_connection_ids=(cid,),
    )
    assert auth.allows_connection(UUID(str(cid))) is True
