"""Filesystem-backed object storage for local dev / tests.

Writes bytes to ``$HARNEX_LOCAL_ARTIFACTS_DIR`` (default ``./artifacts/``) and
mints a signed download URL that points at the FastAPI route in
``api/routes/artifacts.py``. Mirrors the InMemoryVault pattern — staging/prod
must use the Azure backend.
"""

from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote
from uuid import UUID

from harnex_api.config import get_settings
from harnex_api.services.object_storage.base import UploadResult


def _safe_filename(name: str) -> str:
    # Basic sanitization — strip path separators, keep the extension. We never
    # use the filename for filesystem ops directly (we generate a uuid), but it
    # IS used in the user-facing download URL so it should be sane.
    cleaned = name.replace("/", "_").replace("\\", "_").strip()
    return cleaned or "artifact"


def _sign(secret: bytes, payload: str) -> str:
    return hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()


def build_signing_secret() -> bytes:
    """Derive the HMAC secret for signed local URLs.

    Falls back to a derived value from the OpenAI key so local dev gets a
    stable signer without forcing a new env var. Not security-critical: the
    local backend never runs in staging/prod.
    """
    settings = get_settings()
    base = (
        settings.openai_api_key.get_secret_value()
        or settings.keycloak_admin_client_secret.get_secret_value()
        or "harnex-local-dev"
    )
    return hashlib.sha256(base.encode("utf-8")).digest()


def verify_signed_url(
    *, tenant_id: str, storage_key: str, expires: int, signature: str
) -> bool:
    """Constant-time check of the signature on a local download URL."""
    if expires < int(time.time()):
        return False
    expected = _sign(build_signing_secret(), f"{tenant_id}|{storage_key}|{expires}")
    return hmac.compare_digest(expected, signature)


class LocalFilesystemStorage:
    """Filesystem implementation used by local/dev (and tests).

    Layout under the root directory::

        <root>/tenants/<tenant_id>/<yyyy>/<mm>/<uuid>/<filename>
    """

    def __init__(self, root: Path | None = None) -> None:
        if root is None:
            settings = get_settings()
            root_path = getattr(settings, "local_artifacts_dir", "") or "artifacts"
            root = Path(root_path)
        self._root = root.resolve()

    @property
    def root(self) -> Path:
        return self._root

    def path_for(self, storage_key: str) -> Path:
        # storage_key is a relative path under self._root and is fully controlled
        # by us (uuid-based) — no path traversal risk from the caller.
        return self._root / storage_key

    def _sign_url(self, tenant_id: UUID, storage_key: str, ttl_seconds: int) -> str:
        expires = int(time.time()) + max(1, ttl_seconds)
        sig = _sign(build_signing_secret(), f"{tenant_id}|{storage_key}|{expires}")
        settings = get_settings()
        public_base = (
            f"https://{settings.public_host}"
            if settings.public_host
            else f"http://localhost:{settings.api_port}"
        )
        return (
            f"{public_base}/v1/artifacts/{tenant_id}/{quote(storage_key, safe='/')}"
            f"?expires={expires}&signature={sig}"
        )

    async def upload(
        self,
        *,
        tenant_id: UUID,
        filename: str,
        data: bytes,
        content_type: str,
        ttl_seconds: int,
    ) -> UploadResult:
        now = datetime.now(UTC)
        safe_name = _safe_filename(filename)
        artifact_id = uuid.uuid4().hex
        storage_key = (
            f"tenants/{tenant_id}/{now:%Y}/{now:%m}/{artifact_id}/{safe_name}"
        )
        full_path = self._root / storage_key
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)

        url = self._sign_url(tenant_id, storage_key, ttl_seconds)
        return UploadResult(
            download_url=url,
            storage_key=storage_key,
            size_bytes=len(data),
            content_type=content_type,
        )

    async def refresh_url(
        self,
        *,
        tenant_id: UUID,
        storage_key: str,
        content_type: str,
        ttl_seconds: int,
    ) -> str:
        return self._sign_url(tenant_id, storage_key, ttl_seconds)

    async def delete(self, *, tenant_id: UUID, storage_key: str) -> None:
        # Resolve under root and assert containment — same guard as the
        # signed download route. tenant_id is part of the key prefix; reject
        # any storage_key that doesn't share that prefix to keep this method
        # honest about its tenant isolation.
        if not storage_key.startswith(f"tenants/{tenant_id}/"):
            return
        target = (self._root / storage_key).resolve()
        if not str(target).startswith(str(self._root)):
            return
        if target.is_file():
            target.unlink()


__all__ = [
    "LocalFilesystemStorage",
    "build_signing_secret",
    "verify_signed_url",
]
