"""Smoke-test the Infisical vault wiring.

Reads INFISICAL_* from the environment / .env via get_settings(), instantiates
InfisicalVault, and runs a write -> read -> delete -> read round-trip on a
throwaway path. Exits 0 on success, non-zero with a diagnostic on failure.

Usage:
    uv run python scripts/infisical_smoke.py

Run this after filling INFISICAL_PROJECT_ID, INFISICAL_CLIENT_ID, and
INFISICAL_CLIENT_SECRET in .env (and `docker compose up -d infisical`). Same
script verifies Cloud wiring after pointing INFISICAL_BASE_URL at app.infisical.com.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_RUNBOOK = """\
INFISICAL_* envs are not configured. Fill these in .env and re-run:

  INFISICAL_BASE_URL=http://localhost:8090   # or https://app.infisical.com for Cloud
  INFISICAL_PROJECT_ID=<project id>
  INFISICAL_ENVIRONMENT=dev
  INFISICAL_CLIENT_ID=<machine identity client id>
  INFISICAL_CLIENT_SECRET=<machine identity client secret>

Self-host setup (one-time):
  1. http://localhost:8090/admin/signup -> create admin
  2. Create a project; copy its ID into INFISICAL_PROJECT_ID
  3. Settings -> Access Control -> Machine Identities -> add Universal Auth
  4. Copy Client ID / Client Secret into the two envs above
"""


async def main() -> int:
    _load_dotenv()

    # Import after .env is loaded so get_settings() picks the right values.
    from harnex_api.auth.vault import InfisicalVault
    from harnex_api.config import get_settings

    settings = get_settings()
    cid = settings.infisical_client_id.get_secret_value()
    csec = settings.infisical_client_secret.get_secret_value()
    if not (cid and csec and settings.infisical_project_id):
        print(_RUNBOOK, file=sys.stderr)
        return 2

    vault = InfisicalVault(
        base_url=settings.infisical_base_url,
        project_id=settings.infisical_project_id,
        environment=settings.infisical_environment,
        client_id=cid,
        client_secret=csec,
    )

    # Throwaway path under a dedicated namespace so a half-failed run never
    # collides with real connection secrets.
    path = "smoke/round-trip"
    payload = {"k": "v1", "ts": str(asyncio.get_event_loop().time())}

    try:
        await vault.set_secret(path, payload)
    except Exception as exc:
        print(f"set_secret failed: {exc}", file=sys.stderr)
        return 1

    try:
        got = await vault.get_secret(path)
    except Exception as exc:
        print(f"get_secret failed: {exc}", file=sys.stderr)
        return 1
    if got != payload:
        print(f"round-trip mismatch: wrote {payload!r}, read {got!r}", file=sys.stderr)
        return 1

    try:
        await vault.delete_secret(path)
    except Exception as exc:
        print(f"delete_secret failed: {exc}", file=sys.stderr)
        return 1

    after = await vault.get_secret(path)
    if after is not None:
        print(f"delete did not clear: still {after!r}", file=sys.stderr)
        return 1

    print(
        f"OK base_url={settings.infisical_base_url} "
        f"workspace={settings.infisical_project_id} "
        f"environment={settings.infisical_environment}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
