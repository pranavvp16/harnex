from __future__ import annotations

from harnex_api.services.execute.runner import sanitize_headers


def test_sanitize_headers_strips_sensitive_keys_case_insensitive() -> None:
    raw = {
        "Authorization": "Bearer secret",
        "Cookie": "a=b",
        "X-Request-Id": "abc",
        "set-COOKIE": "session=evil",
        "WWW-Authenticate": "Basic realm=x",
        "Proxy-Authorization": "Basic y",
    }
    out = sanitize_headers(raw)
    assert out == {"X-Request-Id": "abc"}
