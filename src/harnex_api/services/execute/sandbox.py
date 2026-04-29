"""Blaxel sandbox wrapper for the execute tool.

The shipped product runs user code-mode JS (and structured-fallback HTTP
requests) inside an ephemeral Blaxel sandbox. This module is the only place
that imports the Blaxel SDK — everything else talks to it through the
`SandboxRunner` Protocol so tests can swap in an `InMemoryRunner`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from harnex_api.config import get_settings


@dataclass(frozen=True)
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int | None = None


@runtime_checkable
class SandboxRunner(Protocol):
    async def run_command(
        self, *, command: str, working_dir: str | None = None, timeout_seconds: int | None = None
    ) -> SandboxResult: ...

    async def run_node_script(
        self, *, source: str, timeout_seconds: int | None = None
    ) -> SandboxResult: ...


class BlaxelSandboxRunner:
    """Default runner — talks to the configured Blaxel sandbox via `blaxel.core`.

    A single shared sandbox is used per environment; per-execution isolation
    relies on Blaxel's process-level sandboxing, plus uniquely-named
    working dirs for the node script path.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._sandbox_name = settings.blaxel_sandbox_name
        self._timeout = settings.blaxel_default_timeout_seconds
        # Bridge our HARNEX_* names into the BL_* vars the SDK reads.
        if not os.environ.get("BL_API_KEY") and settings.blaxel_api_key.get_secret_value():
            os.environ["BL_API_KEY"] = settings.blaxel_api_key.get_secret_value()
        if not os.environ.get("BL_WORKSPACE") and settings.blaxel_workspace:
            os.environ["BL_WORKSPACE"] = settings.blaxel_workspace
        self._sandbox: Any | None = None

    async def _get_sandbox(self) -> Any:
        if self._sandbox is not None:
            return self._sandbox
        from blaxel.core import SandboxInstance  # local import — keeps SDK out of cold-path imports

        self._sandbox = await SandboxInstance.get(self._sandbox_name)
        return self._sandbox

    @staticmethod
    def _to_result(proc: Any) -> SandboxResult:
        # The SDK exposes `logs` on completed processes; older builds use stdout/stderr.
        logs = getattr(proc, "logs", None)
        stdout = getattr(proc, "stdout", None) or (logs or "")
        stderr = getattr(proc, "stderr", "") or ""
        exit_code = int(getattr(proc, "exit_code", 0) or 0)
        return SandboxResult(exit_code=exit_code, stdout=stdout, stderr=stderr)

    async def run_command(
        self,
        *,
        command: str,
        working_dir: str | None = None,
        timeout_seconds: int | None = None,
    ) -> SandboxResult:
        sandbox = await self._get_sandbox()
        spec: dict[str, Any] = {
            "command": command,
            "wait_for_completion": True,
            "timeout": timeout_seconds or self._timeout,
        }
        if working_dir:
            spec["working_dir"] = working_dir
        proc = await sandbox.process.exec(spec)
        return self._to_result(proc)

    async def run_node_script(
        self, *, source: str, timeout_seconds: int | None = None
    ) -> SandboxResult:
        # `node -e <src>` works for short snippets without filesystem writes.
        # The shell escaping is handled by passing through base64 to dodge quoting issues.
        import base64

        encoded = base64.b64encode(source.encode("utf-8")).decode("ascii")
        cmd = (
            "node -e "
            f'"eval(Buffer.from(\\"{encoded}\\", \\"base64\\").toString(\\"utf-8\\"))"'
        )
        return await self.run_command(command=cmd, timeout_seconds=timeout_seconds)


_runner: SandboxRunner | None = None


def get_sandbox_runner() -> SandboxRunner:
    global _runner
    if _runner is None:
        _runner = BlaxelSandboxRunner()
    return _runner


def set_sandbox_runner(runner: SandboxRunner) -> None:
    """Test seam — install a deterministic in-memory runner."""
    global _runner
    _runner = runner


__all__ = [
    "BlaxelSandboxRunner",
    "SandboxResult",
    "SandboxRunner",
    "get_sandbox_runner",
    "set_sandbox_runner",
]
