"""Thin client for Keycloak's Admin REST API.

Used to create users from `/v1/auth/register` so the SPA can render its own
email/password sign-up form. Authenticates as a confidential service-account
client (`harnex-admin-cli` by default) granted the realm-management role
`manage-users`.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from harnex_api.config import AppSettings, get_settings


class EmailAlreadyExistsError(Exception):
    """Raised when Keycloak rejects user creation with HTTP 409."""


class KeycloakAdminError(Exception):
    """Raised when Keycloak returns an unexpected error from the admin API."""


@dataclass
class _CachedToken:
    access_token: str
    expires_at: float


class KeycloakAdminClient:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self._settings = settings or get_settings()
        self._token: _CachedToken | None = None

    @property
    def base_url(self) -> str:
        return self._settings.keycloak_base_url.rstrip("/")

    @property
    def realm(self) -> str:
        return self._settings.keycloak_realm

    async def _get_admin_token(self, client: httpx.AsyncClient) -> str:
        now = time.monotonic()
        if self._token and self._token.expires_at - 30 > now:
            return self._token.access_token

        secret = self._settings.keycloak_admin_client_secret.get_secret_value()
        if not secret:
            raise KeycloakAdminError(
                "KEYCLOAK_ADMIN_CLIENT_SECRET is not set; cannot call admin API"
            )

        token_url = (
            f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token"
        )
        resp = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self._settings.keycloak_admin_client_id,
                "client_secret": secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code != 200:
            raise KeycloakAdminError(
                f"Keycloak admin token request failed ({resp.status_code}): {resp.text}"
            )
        body = resp.json()
        token: str = body["access_token"]
        expires_in: int = int(body.get("expires_in", 60))
        self._token = _CachedToken(access_token=token, expires_at=now + expires_in)
        return token

    async def create_user(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
    ) -> str:
        """Create a Keycloak user; return the new `sub` (user id).

        Splits `full_name` on the last whitespace into first/last so
        Keycloak's UI shows something reasonable.
        """
        first, last = _split_name(full_name)
        async with httpx.AsyncClient(timeout=10.0) as client:
            token = await self._get_admin_token(client)
            users_url = f"{self.base_url}/admin/realms/{self.realm}/users"
            payload = {
                "username": email,
                "email": email,
                "firstName": first,
                "lastName": last,
                "enabled": True,
                "emailVerified": False,
                "credentials": [
                    {"type": "password", "value": password, "temporary": False}
                ],
            }
            resp = await client.post(
                users_url,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 409:
                raise EmailAlreadyExistsError(email)
            if resp.status_code not in (201, 204):
                raise KeycloakAdminError(
                    f"Keycloak create user failed ({resp.status_code}): {resp.text}"
                )

            # Keycloak returns 201 with Location: .../users/{id}; parse the id.
            location: str | None = resp.headers.get("Location") or resp.headers.get("location")
            if location and "/users/" in location:
                return str(location.rsplit("/", 1)[-1])

            # Fallback: query by username.
            list_resp = await client.get(
                users_url,
                params={"username": email, "exact": "true"},
                headers={"Authorization": f"Bearer {token}"},
            )
            list_resp.raise_for_status()
            users = list_resp.json()
            if not users:
                raise KeycloakAdminError("created user not found by username lookup")
            return str(users[0]["id"])


def _split_name(full_name: str) -> tuple[str, str]:
    cleaned = full_name.strip()
    if not cleaned:
        return ("", "")
    parts = cleaned.rsplit(maxsplit=1)
    if len(parts) == 1:
        return (parts[0], "")
    return (parts[0], parts[1])


__all__ = [
    "EmailAlreadyExistsError",
    "KeycloakAdminClient",
    "KeycloakAdminError",
]
