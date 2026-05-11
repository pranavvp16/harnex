"""Pin the path-scoping invariants the InfisicalVault relies on for tenant isolation.

Tenant isolation in production is enforced by the secret_path string layout:
`tenants/{tenant_id}/connections/{conn_id}/...`. Anything that lets a caller
escape that prefix (path traversal, separator injection, leading slash, empty
segment) is a cross-tenant leak. This test pins the helper's rejection
behavior so a future refactor can't accidentally relax it.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from harnex_api.auth.vault import (
    _validate_id_segment,
    connection_secret_path,
    connector_token_path,
)


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "..",
        "../etc",
        "tenant/other",
        "tenant\\other",
        "%2f..%2f",
        "/leading-slash",
        "trailing-slash/",
        "with space",
        "with\ttab",
        "with\x00null",
        "weird:colon",
        "dot.in.middle",
    ],
)
def test_validate_id_segment_rejects_unsafe(bad: str) -> None:
    with pytest.raises(ValueError):
        _validate_id_segment(bad, label="probe")


@pytest.mark.parametrize(
    "good",
    [
        "abc",
        "ABC",
        "0123456789",
        "with-hyphen",
        "with_underscore",
        "Mix_of-EVERY-thing_123",
        str(uuid4()),
    ],
)
def test_validate_id_segment_accepts_safe(good: str) -> None:
    assert _validate_id_segment(good, label="probe") == good


def test_connection_secret_path_layout() -> None:
    tenant = "11111111-1111-1111-1111-111111111111"
    conn = "22222222-2222-2222-2222-222222222222"
    assert connection_secret_path(tenant, conn) == (
        f"tenants/{tenant}/connections/{conn}"
    )


def test_connection_secret_path_distinct_tenants_never_share_prefix() -> None:
    """Tenant A's path must never be a prefix of Tenant B's path."""
    tenant_a = str(uuid4())
    tenant_b = str(uuid4())
    conn = str(uuid4())
    path_a = connection_secret_path(tenant_a, conn)
    path_b = connection_secret_path(tenant_b, conn)
    assert path_a != path_b
    assert not path_a.startswith(path_b + "/")
    assert not path_b.startswith(path_a + "/")


def test_connection_secret_path_traversal_rejected() -> None:
    """A traversal-y tenant_id must raise, not produce a fused path."""
    with pytest.raises(ValueError):
        connection_secret_path("../other-tenant", str(uuid4()))
    with pytest.raises(ValueError):
        connection_secret_path(str(uuid4()), "../../other-conn")


def test_connector_token_path_traversal_rejected() -> None:
    with pytest.raises(ValueError):
        connector_token_path("../escape", "github")
    with pytest.raises(ValueError):
        connector_token_path(str(uuid4()), "../../bad")
