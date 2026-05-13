from __future__ import annotations

from harnex_api.services.execute import (
    SandboxResult,
    SandboxRunner,
    get_sandbox_runner,
    set_sandbox_runner,
)


class FakeRunner:
    """Records calls + returns canned results — verifies the Protocol contract."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def run_command(
        self, *, command: str, working_dir: str | None = None, timeout_seconds: int | None = None
    ) -> SandboxResult:
        self.calls.append(
            {"kind": "command", "command": command, "wd": working_dir, "timeout": timeout_seconds}
        )
        return SandboxResult(exit_code=0, stdout=f"ran:{command}", stderr="")

    async def run_node_script(
        self, *, source: str, timeout_seconds: int | None = None
    ) -> SandboxResult:
        self.calls.append({"kind": "node", "source": source, "timeout": timeout_seconds})
        return SandboxResult(exit_code=0, stdout="42", stderr="")

    async def run_python_script(
        self,
        *,
        source: str,
        working_dir: str | None = None,
        env: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> SandboxResult:
        self.calls.append(
            {
                "kind": "python",
                "source": source,
                "wd": working_dir,
                "env": dict(env or {}),
                "timeout": timeout_seconds,
            }
        )
        return SandboxResult(exit_code=0, stdout="", stderr="")

    async def write_files(self, *, files: dict[str, bytes], working_dir: str) -> None:
        self.calls.append({"kind": "write_files", "wd": working_dir, "count": len(files)})

    async def read_file(self, *, path: str, max_bytes: int) -> bytes:
        self.calls.append({"kind": "read_file", "path": path, "max_bytes": max_bytes})
        return b""

    async def list_files(self, *, working_dir: str) -> list[str]:
        self.calls.append({"kind": "list_files", "wd": working_dir})
        return []


def test_fake_runner_satisfies_protocol() -> None:
    runner = FakeRunner()
    assert isinstance(runner, SandboxRunner)


async def test_set_and_get_runner_roundtrip() -> None:
    runner = FakeRunner()
    set_sandbox_runner(runner)
    try:
        assert get_sandbox_runner() is runner
        result = await get_sandbox_runner().run_command(command="echo hi")
        assert result.exit_code == 0
        assert result.stdout == "ran:echo hi"
        assert runner.calls[0]["command"] == "echo hi"
    finally:
        # Reset so other tests don't see this fake.
        from harnex_api.services.execute import sandbox as sbx

        sbx._runner = None  # type: ignore[attr-defined]


async def test_fake_runner_node_script_path() -> None:
    runner = FakeRunner()
    set_sandbox_runner(runner)
    try:
        result = await get_sandbox_runner().run_node_script(source="console.log(42)")
        assert result.stdout == "42"
        assert runner.calls[0]["kind"] == "node"
        assert "console.log(42)" in runner.calls[0]["source"]
    finally:
        from harnex_api.services.execute import sandbox as sbx

        sbx._runner = None  # type: ignore[attr-defined]
