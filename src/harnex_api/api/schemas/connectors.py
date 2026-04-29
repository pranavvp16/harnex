from __future__ import annotations

from harnex_api.api.schemas.common import ApiModel
from harnex_api.db.models import AuthFlow


class ConnectorOut(ApiModel):
    key: str
    display_name: str
    is_builtin: bool
    default_base_url: str | None
    supported_auth: list[AuthFlow]


__all__ = ["ConnectorOut"]
