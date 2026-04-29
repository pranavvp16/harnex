from __future__ import annotations

from threading import RLock

from harnex_api.connectors.base import BaseConnector, Connector


class ConnectorRegistry:
    """In-process registry of available connectors.

    Built-in connectors register at import time. Future plugin loading can
    add entries dynamically. Lookup is by `key` (e.g. 'github', 'jenkins',
    'generic').
    """

    def __init__(self) -> None:
        self._items: dict[str, Connector] = {}
        self._lock = RLock()

    def register(self, connector: Connector) -> None:
        if not connector.key:
            raise ValueError("connector.key must be a non-empty string")
        with self._lock:
            if connector.key in self._items:
                raise ValueError(f"connector already registered: {connector.key}")
            self._items[connector.key] = connector

    def get(self, key: str) -> Connector:
        try:
            return self._items[key]
        except KeyError as exc:
            raise KeyError(f"unknown connector: {key}") from exc

    def has(self, key: str) -> bool:
        return key in self._items

    def all(self) -> list[Connector]:
        return list(self._items.values())


registry = ConnectorRegistry()


def register_builtins() -> None:
    """Import + register the built-in connectors. Idempotent."""
    from harnex_api.connectors import generic, github, jenkins

    for cls in (generic.GenericConnector, github.GitHubConnector, jenkins.JenkinsConnector):
        instance = cls()
        if not registry.has(instance.key):
            registry.register(instance)


__all__ = ["BaseConnector", "ConnectorRegistry", "register_builtins", "registry"]
