"""Provision (or refresh) the Harnex execute sandboxes in Blaxel.

Two sandboxes are managed:
  - ``harnex-execute``       (Node)   — code-mode HTTP calls + docx skill
  - ``harnex-execute-py``    (Python) — pdf / xlsx / pptx skills

Reads BL_API_KEY and BL_WORKSPACE from the environment (or .env-loaded settings).
Idempotent — uses ``create_if_not_exists`` for both, and ``pip install`` for the
Python sandbox is no-op when the packages are already current.

Usage:
    uv run python scripts/blaxel_provision.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any


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


# Python skill dependencies — installed once per sandbox lifetime; pip is no-op
# when these are already present at compatible versions. Includes pypdf + pillow
# for vendored composio PDF helpers (forms / annotations).
PY_SKILL_PACKAGES = ["reportlab", "openpyxl", "python-pptx", "pypdf", "pillow"]
# docx-js skill dep on the Node sandbox.
NODE_SKILL_PACKAGES = ["docx"]


class _SandboxConfig:
    """Resolved sandbox settings — read *after* .env has been loaded."""

    def __init__(self) -> None:
        self.node_name = os.environ.get("BLAXEL_SANDBOX_NAME", "harnex-execute")
        self.node_image = os.environ.get("BLAXEL_SANDBOX_IMAGE", "blaxel/node:latest")
        self.py_name = os.environ.get("BLAXEL_PYTHON_SANDBOX_NAME", "harnex-execute-py")
        self.py_image = os.environ.get("BLAXEL_PYTHON_SANDBOX_IMAGE", "blaxel/py-app:latest")
        self.memory_mb = int(os.environ.get("BLAXEL_SANDBOX_MEMORY_MB", "2048"))
        self.region = os.environ.get("BLAXEL_SANDBOX_REGION", "us-pdx-1")


async def _provision(
    sandbox_cls: Any,
    *,
    name: str,
    image: str,
    memory_mb: int,
    region: str,
) -> Any:
    sandbox = await sandbox_cls.create_if_not_exists(
        {
            "name": name,
            "image": image,
            "memory": memory_mb,
            "region": region,
        }
    )
    print(f"sandbox ready: {name} ({image})")
    return sandbox


async def _smoke_node(sandbox: Any) -> None:
    proc = await sandbox.process.exec(
        {
            "command": "node -e 'console.log(JSON.stringify({ok:true,ts:Date.now()}))'",
            "wait_for_completion": True,
        }
    )
    print(
        "node smoke:",
        getattr(proc, "logs", None) or getattr(proc, "stdout", None) or proc,
    )


async def _install_node_packages(sandbox: Any) -> None:
    if not NODE_SKILL_PACKAGES:
        return
    pkgs = " ".join(NODE_SKILL_PACKAGES)
    proc = await sandbox.process.exec(
        {
            "command": f"npm install --silent {pkgs}",
            "wait_for_completion": True,
            "timeout": 180,
        }
    )
    print(
        "npm install:",
        getattr(proc, "stderr", "") or getattr(proc, "logs", None) or "ok",
    )


async def _smoke_python(sandbox: Any) -> None:
    proc = await sandbox.process.exec(
        {
            "command": 'python3 -c \'import sys,json;print(json.dumps({"ok":True,"py":sys.version}))\'',
            "wait_for_completion": True,
        }
    )
    print(
        "python smoke:",
        getattr(proc, "logs", None) or getattr(proc, "stdout", None) or proc,
    )


async def _install_python_packages(sandbox: Any) -> None:
    pkgs = " ".join(PY_SKILL_PACKAGES)
    # `--break-system-packages` is needed on Debian/Ubuntu-based images that
    # mark the system Python as PEP 668-managed. Harmless on others.
    proc = await sandbox.process.exec(
        {
            "command": f"pip3 install --break-system-packages --quiet {pkgs}",
            "wait_for_completion": True,
            "timeout": 300,
        }
    )
    print(
        "pip install:",
        getattr(proc, "stderr", "") or getattr(proc, "logs", None) or "ok",
    )


async def main() -> int:
    _load_dotenv()
    # Resolve sandbox settings after .env has been loaded; otherwise overrides
    # like BLAXEL_PYTHON_SANDBOX_NAME placed in .env would be missed here while
    # the running API (which reads them via pydantic settings) sees them.
    cfg = _SandboxConfig()

    if "BL_API_KEY" not in os.environ and os.environ.get("BLAXEL_API_KEY"):
        os.environ["BL_API_KEY"] = os.environ["BLAXEL_API_KEY"]
    if "BL_WORKSPACE" not in os.environ:
        ws_url = os.environ.get("BLAXEL_WORKSPACE_URL", "")
        parts = [p for p in ws_url.split("/") if p]
        if len(parts) >= 3:
            os.environ["BL_WORKSPACE"] = parts[2]

    if not os.environ.get("BL_API_KEY") or not os.environ.get("BL_WORKSPACE"):
        print("missing BL_API_KEY or BL_WORKSPACE", file=sys.stderr)
        return 2

    from blaxel.core import SandboxInstance

    node_sandbox = await _provision(
        SandboxInstance,
        name=cfg.node_name,
        image=cfg.node_image,
        memory_mb=cfg.memory_mb,
        region=cfg.region,
    )
    await _smoke_node(node_sandbox)
    await _install_node_packages(node_sandbox)

    py_sandbox = await _provision(
        SandboxInstance,
        name=cfg.py_name,
        image=cfg.py_image,
        memory_mb=cfg.memory_mb,
        region=cfg.region,
    )
    await _smoke_python(py_sandbox)
    await _install_python_packages(py_sandbox)

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
