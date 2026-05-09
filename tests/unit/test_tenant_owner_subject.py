"""Shape of anonymous owner ids for tenant onboarding (Codex: VARCHAR(128) cap)."""

from harnex_api.api.routes.tenants import _MAX_KEYCLOAK_USER_ID_LEN, _owner_subject_key


def test_owner_email_truncated_to_column_width() -> None:
    mail = "x" * 200
    got = _owner_subject_key(mail, "ignored")
    assert len(got) == _MAX_KEYCLOAK_USER_ID_LEN


def test_anon_long_name_stays_within_column() -> None:
    name = "A" * 200
    got = _owner_subject_key(None, name)
    assert len(got) <= _MAX_KEYCLOAK_USER_ID_LEN
    assert got.startswith("anon:")


def test_anon_short_name_is_literal() -> None:
    assert _owner_subject_key(None, "Ada Lovelace") == "anon:ada lovelace"
