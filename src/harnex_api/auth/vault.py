from __future__ import annotations

from typing import Protocol

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


_vault: SecretsVault = InMemoryVault()


def set_vault(vault: SecretsVault) -> None:
    global _vault
    _vault = vault


def get_vault() -> SecretsVault:
    return _vault


def connection_secret_path(tenant_id: str, connection_id: str) -> str:
    return f"tenants/{tenant_id}/connections/{connection_id}"


def connector_token_path(tenant_id: str, connector_key: str) -> str:
    return f"tenants/{tenant_id}/connectors/{connector_key}/tokens"


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
    "SecretsVault",
    "connection_secret_path",
    "connector_token_path",
    "get_vault",
    "load_connection_credentials",
    "set_vault",
]
