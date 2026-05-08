"""Provision (or refresh) the shared Harnex execute sandbox in Blaxel.

Reads BL_API_KEY and BL_WORKSPACE from the environment (or .env-loaded settings).
Idempotent — safe to re-run; uses `create_if_not_exists`.

Usage:
    uv run python scripts/blaxel_provision.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path


# Bootstrap env from .env if present; CI passes vars explicitly.
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


SANDBOX_NAME = "harnex-execute"
# `blaxel/node:latest` ships node — that's what code-mode JS validators run on.
SANDBOX_IMAGE = "blaxel/node:latest"
SANDBOX_MEMORY_MB = 2048
SANDBOX_REGION = "us-pdx-1"


async def main() -> int:
    _load_dotenv()
    # The SDK looks for BL_API_KEY + BL_WORKSPACE; bridge from our HARNEX naming.
    if "BL_API_KEY" not in os.environ and os.environ.get("BLAXEL_API_KEY"):
        os.environ["BL_API_KEY"] = os.environ["BLAXEL_API_KEY"]
    if "BL_WORKSPACE" not in os.environ:
        ws_url = os.environ.get("BLAXEL_WORKSPACE_URL", "")
        # https://app.blaxel.ai/<workspace>/<project> -> <workspace>
        parts = [p for p in ws_url.split("/") if p]
        if len(parts) >= 3:
            os.environ["BL_WORKSPACE"] = parts[2]

    if not os.environ.get("BL_API_KEY") or not os.environ.get("BL_WORKSPACE"):
        print("missing BL_API_KEY or BL_WORKSPACE", file=sys.stderr)
        return 2

    from blaxel.core import SandboxInstance

    sandbox = await SandboxInstance.create_if_not_exists(
        {
            "name": SANDBOX_NAME,
            "image": SANDBOX_IMAGE,
            "memory": SANDBOX_MEMORY_MB,
            "region": SANDBOX_REGION,
        }
    )
    print(f"sandbox ready: {SANDBOX_NAME}")
    # Smoke test: run `node -e 'console.log(...)'` to confirm the runtime works.
    proc = await sandbox.process.exec(
        {
            "command": "node -e 'console.log(JSON.stringify({ok: true, ts: Date.now()}))'",
            "wait_for_completion": True,
        }
    )
    print("smoke output:", getattr(proc, "logs", None) or getattr(proc, "stdout", None) or proc)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
