"""Idempotent connector-catalog seeding.

The `connections.connector_key` column is a foreign key to `connectors.key`,
so the catalog table must contain a row for every built-in connector before
tenants can create connections. This module mirrors the in-process registry
into the DB at startup; it is safe to call repeatedly.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.connectors.registry import register_builtins, registry
from harnex_api.db.models import Connector


async def ensure_connector_catalog(session: AsyncSession) -> None:
    register_builtins()
    existing_keys = {
        row[0] for row in (await session.execute(select(Connector.key))).all()
    }
    for connector in registry.all():
        if connector.key in existing_keys:
            continue
        session.add(
            Connector(
                key=connector.key,
                display_name=connector.display_name or connector.key,
                is_builtin=True,
                default_base_url=connector.default_base_url,
                supported_auth=[flow.value for flow in connector.supported_auth],
            )
        )
    await session.flush()


__all__ = ["ensure_connector_catalog"]
