"""Idempotent post-startup wiring for the Harnex Keycloak realm.

Run after `docker compose up -d` once the `harnex` realm has been imported.

What it does (only the bits that can't live in the realm import JSON
because they involve secrets or auto-generated service-account users):

1. Sets the `harnex-admin-cli` client secret to `KEYCLOAK_ADMIN_CLIENT_SECRET`
   so the API can mint admin tokens.
2. Grants the `harnex-admin-cli` service account the `realm-management.manage-users`
   role so it can create users via `POST /admin/realms/harnex/users`.
3. Creates / updates the Google identity provider when
   `GOOGLE_OAUTH_CLIENT_ID` + `GOOGLE_OAUTH_CLIENT_SECRET` are set.
4. Creates / updates the GitHub identity provider when
   `GITHUB_OAUTH_CLIENT_ID` + `GITHUB_OAUTH_CLIENT_SECRET` are set.

Safe to re-run; treats existing resources as updates.

Usage:
    uv run python scripts/keycloak_setup.py
"""

from __future__ import annotations

import os
import sys
from typing import Any

import httpx

KEYCLOAK_BASE_URL = os.environ.get("KEYCLOAK_BASE_URL", "http://localhost:8080").rstrip("/")
REALM = os.environ.get("KEYCLOAK_REALM", "harnex")
ADMIN_USER = os.environ.get("KEYCLOAK_ADMIN", "admin")
ADMIN_PASSWORD = os.environ.get("KEYCLOAK_ADMIN_PASSWORD")
ADMIN_CLIENT_ID = os.environ.get("KEYCLOAK_ADMIN_CLIENT_ID", "harnex-admin-cli")
ADMIN_CLIENT_SECRET = os.environ.get("KEYCLOAK_ADMIN_CLIENT_SECRET")
WEB_CLIENT_ID = os.environ.get("KEYCLOAK_WEB_CLIENT_ID", "harnex-web")
WEB_CLIENT_SECRET = os.environ.get("KEYCLOAK_WEB_CLIENT_SECRET")

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GITHUB_CLIENT_ID = os.environ.get("GITHUB_OAUTH_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_OAUTH_CLIENT_SECRET")


class KeycloakError(RuntimeError):
    pass


def _admin_token(client: httpx.Client) -> str:
    if not ADMIN_PASSWORD:
        raise KeycloakError("KEYCLOAK_ADMIN_PASSWORD is required")
    resp = client.post(
        f"{KEYCLOAK_BASE_URL}/realms/master/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": ADMIN_USER,
            "password": ADMIN_PASSWORD,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if resp.status_code != 200:
        raise KeycloakError(f"admin login failed ({resp.status_code}): {resp.text}")
    token: str = resp.json()["access_token"]
    return token


def _api(client: httpx.Client, token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _get_client_uuid(client: httpx.Client, token: str, client_id: str) -> str:
    resp = client.get(
        f"{KEYCLOAK_BASE_URL}/admin/realms/{REALM}/clients",
        params={"clientId": client_id},
        headers=_api(client, token),
    )
    resp.raise_for_status()
    rows = resp.json()
    if not rows:
        raise KeycloakError(f"client {client_id!r} not found in realm {REALM!r}")
    return str(rows[0]["id"])


def _set_admin_cli_secret(client: httpx.Client, token: str) -> None:
    if not ADMIN_CLIENT_SECRET:
        print(f"  - SKIP: {ADMIN_CLIENT_ID} secret (KEYCLOAK_ADMIN_CLIENT_SECRET not set)")
        return
    uuid = _get_client_uuid(client, token, ADMIN_CLIENT_ID)
    # Fetch, mutate, PUT — Keycloak 25 expects the full client representation.
    detail = client.get(
        f"{KEYCLOAK_BASE_URL}/admin/realms/{REALM}/clients/{uuid}",
        headers=_api(client, token),
    )
    detail.raise_for_status()
    body: dict[str, Any] = detail.json()
    body["secret"] = ADMIN_CLIENT_SECRET
    body["serviceAccountsEnabled"] = True
    resp = client.put(
        f"{KEYCLOAK_BASE_URL}/admin/realms/{REALM}/clients/{uuid}",
        json=body,
        headers=_api(client, token),
    )
    if resp.status_code not in (204, 200):
        raise KeycloakError(f"set client secret failed ({resp.status_code}): {resp.text}")
    print(f"  - OK:   {ADMIN_CLIENT_ID} secret set")


def _set_web_client_secret(client: httpx.Client, token: str) -> None:
    """Ensure harnex-web is a confidential client and align its secret with .env.

    The BFF cookie session flow posts to the token endpoint with this secret;
    without it /v1/session/callback fails with `KEYCLOAK_WEB_CLIENT_SECRET is
    not configured` after Keycloak has already authenticated the user.
    """
    if not WEB_CLIENT_SECRET:
        print(f"  - SKIP: {WEB_CLIENT_ID} secret (KEYCLOAK_WEB_CLIENT_SECRET not set)")
        return
    uuid = _get_client_uuid(client, token, WEB_CLIENT_ID)
    detail = client.get(
        f"{KEYCLOAK_BASE_URL}/admin/realms/{REALM}/clients/{uuid}",
        headers=_api(client, token),
    )
    detail.raise_for_status()
    body: dict[str, Any] = detail.json()
    body["publicClient"] = False
    body["clientAuthenticatorType"] = "client-secret"
    body["secret"] = WEB_CLIENT_SECRET
    resp = client.put(
        f"{KEYCLOAK_BASE_URL}/admin/realms/{REALM}/clients/{uuid}",
        json=body,
        headers=_api(client, token),
    )
    if resp.status_code not in (204, 200):
        raise KeycloakError(f"set web client secret failed ({resp.status_code}): {resp.text}")
    print(f"  - OK:   {WEB_CLIENT_ID} confidential + secret set")


def _grant_manage_users(client: httpx.Client, token: str) -> None:
    """Grant realm-management.manage-users to the admin-cli service account."""
    sa_user_resp = client.get(
        f"{KEYCLOAK_BASE_URL}/admin/realms/{REALM}/clients/{_get_client_uuid(client, token, ADMIN_CLIENT_ID)}/service-account-user",
        headers=_api(client, token),
    )
    sa_user_resp.raise_for_status()
    sa_user_id = sa_user_resp.json()["id"]

    rm_uuid = _get_client_uuid(client, token, "realm-management")
    role_resp = client.get(
        f"{KEYCLOAK_BASE_URL}/admin/realms/{REALM}/clients/{rm_uuid}/roles/manage-users",
        headers=_api(client, token),
    )
    role_resp.raise_for_status()
    role = role_resp.json()

    grant = client.post(
        f"{KEYCLOAK_BASE_URL}/admin/realms/{REALM}/users/{sa_user_id}/role-mappings/clients/{rm_uuid}",
        json=[{"id": role["id"], "name": role["name"]}],
        headers=_api(client, token),
    )
    if grant.status_code not in (204, 200, 409):
        raise KeycloakError(f"grant manage-users failed ({grant.status_code}): {grant.text}")
    print(f"  - OK:   {ADMIN_CLIENT_ID} granted realm-management.manage-users")


def _upsert_idp(
    client: httpx.Client,
    token: str,
    *,
    alias: str,
    provider_id: str,
    display_name: str,
    client_id: str,
    client_secret: str,
    extra_config: dict[str, str] | None = None,
) -> None:
    config = {
        "clientId": client_id,
        "clientSecret": client_secret,
        "syncMode": "IMPORT",
    }
    if extra_config:
        config.update(extra_config)

    payload = {
        "alias": alias,
        "providerId": provider_id,
        "displayName": display_name,
        "enabled": True,
        "trustEmail": True,
        "storeToken": False,
        "addReadTokenRoleOnCreate": False,
        "linkOnly": False,
        "firstBrokerLoginFlowAlias": "first broker login",
        "config": config,
    }

    existing = client.get(
        f"{KEYCLOAK_BASE_URL}/admin/realms/{REALM}/identity-provider/instances/{alias}",
        headers=_api(client, token),
    )
    if existing.status_code == 404:
        resp = client.post(
            f"{KEYCLOAK_BASE_URL}/admin/realms/{REALM}/identity-provider/instances",
            json=payload,
            headers=_api(client, token),
        )
        if resp.status_code not in (201, 204):
            raise KeycloakError(f"create IDP {alias} failed ({resp.status_code}): {resp.text}")
        print(f"  - OK:   IDP {alias} created")
    elif existing.status_code == 200:
        resp = client.put(
            f"{KEYCLOAK_BASE_URL}/admin/realms/{REALM}/identity-provider/instances/{alias}",
            json=payload,
            headers=_api(client, token),
        )
        if resp.status_code not in (204, 200):
            raise KeycloakError(f"update IDP {alias} failed ({resp.status_code}): {resp.text}")
        print(f"  - OK:   IDP {alias} updated")
    else:
        raise KeycloakError(
            f"check IDP {alias} failed ({existing.status_code}): {existing.text}"
        )


def _setup_google(client: httpx.Client, token: str) -> None:
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        print("  - SKIP: Google IDP (GOOGLE_OAUTH_CLIENT_ID/SECRET not set)")
        return
    _upsert_idp(
        client,
        token,
        alias="google",
        provider_id="google",
        display_name="Google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        # `prompt=select_account` forces Google's account chooser on every
        # broker hand-off so a logged-out user can switch between multiple
        # Google accounts. Without it, Google silently re-uses whichever
        # account has an active browser session.
        extra_config={
            "defaultScope": "openid profile email",
            "prompt": "select_account",
        },
    )


def _setup_github(client: httpx.Client, token: str) -> None:
    if not (GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET):
        print("  - SKIP: GitHub IDP (GITHUB_OAUTH_CLIENT_ID/SECRET not set)")
        return
    _upsert_idp(
        client,
        token,
        alias="github",
        provider_id="github",
        display_name="GitHub",
        client_id=GITHUB_CLIENT_ID,
        client_secret=GITHUB_CLIENT_SECRET,
        extra_config={"defaultScope": "user:email"},
    )


def main() -> int:
    print(f"keycloak_setup: {KEYCLOAK_BASE_URL} realm={REALM}")
    with httpx.Client(timeout=10.0) as client:
        try:
            token = _admin_token(client)
        except KeycloakError as exc:
            print(f"FATAL: {exc}", file=sys.stderr)
            return 1

        try:
            _set_admin_cli_secret(client, token)
            _set_web_client_secret(client, token)
            _grant_manage_users(client, token)
            _setup_google(client, token)
            _setup_github(client, token)
        except (KeycloakError, httpx.HTTPError) as exc:
            print(f"FATAL: {exc}", file=sys.stderr)
            return 1

    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
