"""Provision (or refresh) the Harnex execute sandboxes in Blaxel.

Two sandboxes are managed:
  - ``harnex-execute``       (Node)   — code-mode HTTP calls + docx skill
  - ``harnex-execute-py``    (Python) — pdf / xlsx / pptx skills

Reads BL_API_KEY and BL_WORKSPACE from the environment (or .env-loaded settings).
Idempotent — uses ``create_if_not_exists`` for both. On Debian-based Python
sandboxes we ``apt-get install`` ``poppler-utils`` (for ``pdf2image`` / ``pdftoppm``)
and ``libreoffice-calc`` (headless ``soffice`` for ``recalc.py``), then ``pip install``.
Skip system packages with ``BLAXEL_SKIP_PYTHON_SYSTEM_PACKAGES=1``.

Usage:
    uv run python scripts/blaxel_provision.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any


def _proc_exit_code(proc: Any) -> int:
    return int(getattr(proc, "exit_code", 0) or 0)


def _proc_text(proc: Any) -> str:
    logs = getattr(proc, "logs", None)
    if logs:
        return str(logs).strip()
    parts = []
    for attr in ("stderr", "stdout"):
        v = getattr(proc, attr, None)
        if v:
            parts.append(str(v))
    joined = "\n".join(parts).strip()
    return joined or str(proc)


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
# for vendored composio PDF helpers (forms / annotations), and pdf2image for
# ``convert_pdf_to_images.py``. Poppler (~``pdftoppm``) and LibreOffice (``soffice``)
# come from APT via `_install_python_system_packages`, not PyPI.
PY_SKILL_PACKAGES = ["reportlab", "openpyxl", "python-pptx", "pypdf", "pillow", "pdf2image"]
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


def _skip_python_system_packages() -> bool:
    raw = os.environ.get("BLAXEL_SKIP_PYTHON_SYSTEM_PACKAGES", "").strip().lower()
    return raw in ("1", "true", "yes", "on")


async def _install_python_system_packages(sandbox: Any) -> bool | None:
    """Debian APT deps for bundled skill helpers (pdf2image, xlsx LibreOffice).

    Requires root + ``apt-get`` in the sandbox image (``blaxel/py-app:latest`` is
    typically Debian-based). Non-APT images skip with a log line.

    Returns ``True`` if packages were installed (caller should verify), ``False`` if
    skipped or not applicable, ``None`` if apt failed non-zero.
    """
    if _skip_python_system_packages():
        print(
            "apt install: skipped (BLAXEL_SKIP_PYTHON_SYSTEM_PACKAGES); "
            "ensure poppler-utils + libreoffice-calc (soffice) for PDF / XLSX skills"
        )
        return False

    probe = await sandbox.process.exec(
        {"command": "bash -lc 'command -v apt-get'", "wait_for_completion": True}
    )
    if _proc_exit_code(probe) != 0:
        print(
            "blaxel_provision: no apt-get on this image; skipping system packages "
            "(use Debian-based BLAXEL_PYTHON_SANDBOX_IMAGE or install poppler/soffice in a custom image)"
        )
        return False

    apt_cmd = (
        "bash -lc '"
        "export DEBIAN_FRONTEND=noninteractive; "
        "apt-get update -qq && "
        "apt-get install -y --no-install-recommends poppler-utils libreoffice-calc'"
    )
    proc = await sandbox.process.exec(
        {
            "command": apt_cmd,
            "wait_for_completion": True,
            "timeout": 900,
        }
    )
    print("apt install (poppler-utils, libreoffice-calc):", _proc_text(proc))
    code = _proc_exit_code(proc)
    if code != 0:
        print(
            "blaxel_provision: apt install failed "
            f"(exit {code}); bundled PDF/XLSX helpers may not run.",
            file=sys.stderr,
        )
        return None
    return True


async def _verify_python_skill_toolchain(sandbox: Any) -> int:
    """Sanity-check Poppler, LibreOffice, and PyPI skill imports after provision."""
    verify_cmd = (
        "bash -lc '"
        "command -v pdftoppm >/dev/null && "
        "command -v soffice >/dev/null && "
        'python3 -c "import PIL, pdf2image, openpyxl, pptx, pypdf, reportlab"'
        "'"
    )
    proc = await sandbox.process.exec(
        {"command": verify_cmd, "wait_for_completion": True, "timeout": 120}
    )
    print("python skill toolchain verify:", _proc_text(proc) or "(no output)")
    return _proc_exit_code(proc)


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
    sys_pkgs = await _install_python_system_packages(py_sandbox)
    if sys_pkgs is None:
        return 3
    await _install_python_packages(py_sandbox)
    if sys_pkgs is True and await _verify_python_skill_toolchain(py_sandbox) != 0:
        print(
            "blaxel_provision: post-apt toolchain verify failed "
            "(check pdftoppm, soffice, pip packages above)",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
