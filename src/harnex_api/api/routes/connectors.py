from __future__ import annotations

from fastapi import APIRouter

from harnex_api.api.schemas.connectors import ConnectorOut
from harnex_api.connectors.registry import register_builtins, registry

router = APIRouter(prefix="/v1/connectors", tags=["connectors"])


@router.get("", response_model=list[ConnectorOut])
async def list_connectors() -> list[ConnectorOut]:
    """Catalog of registered connectors. Used by the wizard to render tiles."""
    register_builtins()
    return [
        ConnectorOut(
            key=c.key,
            display_name=c.display_name,
            is_builtin=True,
            default_base_url=c.default_base_url,
            supported_auth=list(c.supported_auth),
        )
        for c in registry.all()
    ]


__all__ = ["router"]
