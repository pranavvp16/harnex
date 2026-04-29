from __future__ import annotations

from harnex_api.services.api_keys import (
    PREFIX_BYTES,
    TOKEN_PREFIX,
    issue_key,
    parse_prefix,
    verify_key,
)


def _b64url_chars(n_bytes: int) -> int:
    # base64url without padding produces ceil(n_bytes * 4 / 3) chars.
    return (n_bytes * 4 + 2) // 3


def test_issue_key_format() -> None:
    issued = issue_key()
    assert issued.plaintext.startswith(f"{TOKEN_PREFIX}.")
    parts = issued.plaintext.split(".")
    assert len(parts) == 3
    assert parts[0] == TOKEN_PREFIX
    assert len(parts[1]) == _b64url_chars(PREFIX_BYTES)
    assert issued.prefix == parts[1]
    assert "$" in issued.hash_blob


def test_verify_key_round_trip() -> None:
    issued = issue_key()
    assert verify_key(issued.plaintext, issued.hash_blob) is True


def test_verify_key_rejects_tampered() -> None:
    issued = issue_key()
    tampered = issued.plaintext[:-1] + ("A" if issued.plaintext[-1] != "A" else "B")
    assert verify_key(tampered, issued.hash_blob) is False


def test_verify_key_rejects_malformed_blob() -> None:
    assert verify_key("hnx.abc.xyz", "not-a-real-blob") is False


def test_parse_prefix_extracts_lookup_segment() -> None:
    issued = issue_key()
    assert parse_prefix(issued.plaintext) == issued.prefix


def test_parse_prefix_rejects_malformed() -> None:
    assert parse_prefix("not-a-key") is None
    assert parse_prefix("xyz.abc.def") is None  # wrong product prefix


def test_two_keys_have_different_hashes() -> None:
    a = issue_key()
    b = issue_key()
    assert a.plaintext != b.plaintext
    assert a.hash_blob != b.hash_blob
