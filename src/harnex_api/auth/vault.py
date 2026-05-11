from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import httpx

from harnex_api.db.models import AuthFlow


class SecretsVault(Protocol):
    """Adapter contract — switching between local Infisical, hosted Infisical,
    or test in-memory storage is purely an env-config change."""

    async def get_secret(self, path: str) -> dict[str, str] | None: ...
    async def set_secret(self, path: str, values: dict[str, str]) -> None: ...
    async def delete_secret(self, path: str) -> None: ...


class InMemoryVault:
    """Used by tests and local smoke runs when Infisical isn't configured."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, str]] = {}

    async def get_secret(self, path: str) -> dict[str, str] | None:
        return dict(self._data[path]) if path in self._data else None

    async def set_secret(self, path: str, values: dict[str, str]) -> None:
        self._data[path] = dict(values)

    async def delete_secret(self, path: str) -> None:
        self._data.pop(path, None)


class InfisicalVault:
    """Secrets vault backed by self-hosted Infisical via the REST API.

    Uses Universal Auth (machine identity). Each vault path maps to an Infisical
    folder; the full credential bag is stored as a single JSON-encoded secret
    named CREDENTIALS within that folder.
    """

    _KEY = "CREDENTIALS"

    def __init__(
        self,
        base_url: str,
        project_id: str,
        environment: str,
        client_id: str,
        client_secret: str,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._project_id = project_id
        self._environment = environment
        self._client_id = client_id
        self._client_secret = client_secret
        self._token: str | None = None

    async def _refresh_token(self) -> str:
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{self._base_url}/api/v1/auth/universal-auth/login",
                json={"clientId": self._client_id, "clientSecret": self._client_secret},
                timeout=10.0,
            )
            r.raise_for_status()
            self._token = str(r.json()["accessToken"])
            return self._token

    async def _token_headers(self) -> dict[str, str]:
        if not self._token:
            await self._refresh_token()
        return {"Authorization": f"Bearer {self._token}"}

    @staticmethod
    def _folder(path: str) -> str:
        return "/" + path.strip("/")

    async def _with_token_retry(
        self, call: Callable[[], Awaitable[httpx.Response]]
    ) -> httpx.Response:
        r = await call()
        if r.status_code != 401:
            return r
        self._token = None
        await self._refresh_token()
        return await call()

    async def _get(self, path: str) -> httpx.Response:
        params: dict[str, str] = {
            "workspaceId": self._project_id,
            "environment": self._environment,
            "secretPath": self._folder(path),
        }

        async def once() -> httpx.Response:
            hdrs = await self._token_headers()
            async with httpx.AsyncClient() as c:
                return await c.get(
                    f"{self._base_url}/api/v3/secrets/raw/{self._KEY}",
                    headers=hdrs,
                    params=params,
                    timeout=10.0,
                )

        return await self._with_token_retry(once)

    async def _ensure_folder(self, parent: str, name: str) -> None:
        """Create one folder segment under `parent`. Already-exists is a no-op.

        Infisical refuses to write a secret to a nested path unless every parent
        folder exists, so set_secret walks the path and calls this for each
        segment. The folder API isn't idempotent — a duplicate name returns
        400 with a "already exists" message, which we treat as success.
        """
        body: dict[str, Any] = {
            "workspaceId": self._project_id,
            "environment": self._environment,
            "path": parent or "/",
            "name": name,
        }

        async def once() -> httpx.Response:
            hdrs = await self._token_headers()
            async with httpx.AsyncClient() as c:
                return await c.post(
                    f"{self._base_url}/api/v1/folders",
                    headers=hdrs,
                    json=body,
                    timeout=10.0,
                )

        r = await self._with_token_retry(once)
        if r.status_code in (200, 201):
            return
        if r.status_code == 400 and "already exists" in r.text:
            return
        r.raise_for_status()

    async def _ensure_folder_tree(self, path: str) -> None:
        """Walk `path` segments and create each folder top-down.

        e.g. path="tenants/abc/connections/xyz" → creates `/tenants`, then
        `/tenants/abc`, then `/tenants/abc/connections`, then
        `/tenants/abc/connections/xyz`. Each step is idempotent.
        """
        segments = [s for s in path.strip("/").split("/") if s]
        parent = ""
        for seg in segments:
            await self._ensure_folder(parent or "/", seg)
            parent = f"{parent}/{seg}" if parent else f"/{seg}"

    async def _upsert(self, path: str, values: dict[str, str]) -> httpx.Response:
        await self._ensure_folder_tree(path)
        body: dict[str, Any] = {
            "workspaceId": self._project_id,
            "environment": self._environment,
            "secretPath": self._folder(path),
            "secretValue": json.dumps(values),
            "type": "shared",
        }

        async def once() -> httpx.Response:
            hdrs = await self._token_headers()
            async with httpx.AsyncClient() as c:
                r = await c.patch(
                    f"{self._base_url}/api/v3/secrets/raw/{self._KEY}",
                    headers=hdrs,
                    json=body,
                    timeout=10.0,
                )
                if r.status_code == 404:
                    r = await c.post(
                        f"{self._base_url}/api/v3/secrets/raw/{self._KEY}",
                        headers=hdrs,
                        json=body,
                        timeout=10.0,
                    )
                return r

        return await self._with_token_retry(once)

    async def get_secret(self, path: str) -> dict[str, str] | None:
        r = await self._get(path)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return dict(json.loads(r.json()["secret"]["secretValue"]))

    async def set_secret(self, path: str, values: dict[str, str]) -> None:
        r = await self._upsert(path, values)
        r.raise_for_status()

    async def delete_secret(self, path: str) -> None:
        body: dict[str, Any] = {
            "workspaceId": self._project_id,
            "environment": self._environment,
            "secretPath": self._folder(path),
        }

        async def once() -> httpx.Response:
            hdrs = await self._token_headers()
            async with httpx.AsyncClient() as c:
                return await c.request(
                    "DELETE",
                    f"{self._base_url}/api/v3/secrets/raw/{self._KEY}",
                    headers=hdrs,
                    json=body,
                    timeout=10.0,
                )

        r = await self._with_token_retry(once)
        if r.status_code == 404:
            return
        r.raise_for_status()


_vault: SecretsVault = InMemoryVault()


def set_vault(vault: SecretsVault) -> None:
    global _vault
    _vault = vault


def get_vault() -> SecretsVault:
    return _vault


# UUIDs, connector slugs, and Infisical path segments we construct: no
# URL-encoded separators (%2f), no whitespace/control, no traversal.
_SAFE_VAULT_SEGMENT = re.compile(r"^[A-Za-z0-9_-]+\Z")


def _validate_id_segment(value: str, *, label: str) -> str:
    """Reject values that could escape the per-tenant path namespace.

    Vault paths are built by string interpolation. A denylist is easy to
    bypass (e.g. ``%2f``); allowlist segments to alphanumeric, hyphen, underscore.
    """
    if not value or not _SAFE_VAULT_SEGMENT.fullmatch(value):
        raise ValueError(f"invalid vault path segment for {label}: {value!r}")
    return value


def connection_secret_path(tenant_id: str, connection_id: str) -> str:
    t = _validate_id_segment(tenant_id, label="tenant_id")
    c = _validate_id_segment(connection_id, label="connection_id")
    return f"tenants/{t}/connections/{c}"


def connector_token_path(tenant_id: str, connector_key: str) -> str:
    t = _validate_id_segment(tenant_id, label="tenant_id")
    k = _validate_id_segment(connector_key, label="connector_key")
    return f"tenants/{t}/connectors/{k}/tokens"


async def load_connection_credentials(
    tenant_id: str, connection_id: str, auth_flow: AuthFlow
) -> dict[str, str]:
    """Resolve the secret bag for one connection. Returns {} if vault is empty
    (e.g. AuthFlow.none or unconfigured connection in tests).
    """
    if auth_flow == AuthFlow.none:
        return {}
    path = connection_secret_path(tenant_id, connection_id)
    values = await get_vault().get_secret(path)
    return values or {}


__all__ = [
    "InMemoryVault",
    "InfisicalVault",
    "SecretsVault",
    "connection_secret_path",
    "connector_token_path",
    "get_vault",
    "load_connection_credentials",
    "set_vault",
]
