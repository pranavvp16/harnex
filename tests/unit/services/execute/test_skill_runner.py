"""Skill runner orchestration — sandbox writes the file, storage uploads it.

The DB session is mocked because the unit suite doesn't hit Postgres; the
sandbox and object-storage seams use the real Protocol-backed test fakes so
the wire-up they exercise is the same one production uses.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from harnex_api.db.models import ExecutionStatus, Skill, SkillRuntime
from harnex_api.services.execute import sandbox as sbx
from harnex_api.services.execute.sandbox import (
    SandboxResult,
    set_python_sandbox_runner,
    set_sandbox_runner,
)
from harnex_api.services.execute.skill_runner import SkillNotFoundError, execute_skill
from harnex_api.services.object_storage import UploadResult
from harnex_api.services.object_storage.provider import set_object_storage


class _RecordingRunner:
    """SandboxRunner stub that records writes/reads and returns canned results."""

    def __init__(
        self,
        *,
        produces_files: list[str] | None = None,
        artifact_bytes: bytes = b"%PDF-fake\n",
        script_exit_code: int = 0,
        script_stderr: str = "",
    ) -> None:
        self.calls: list[dict[str, Any]] = []
        self._files = list(produces_files or [])
        self._artifact = artifact_bytes
        self._script_exit_code = script_exit_code
        self._script_stderr = script_stderr

    async def run_command(
        self, *, command: str, working_dir: str | None = None, timeout_seconds: int | None = None
    ) -> SandboxResult:
        self.calls.append({"kind": "command", "cmd": command, "wd": working_dir})
        return SandboxResult(exit_code=0, stdout="", stderr="")

    async def run_node_script(
        self, *, source: str, timeout_seconds: int | None = None
    ) -> SandboxResult:
        self.calls.append({"kind": "node", "source": source})
        return SandboxResult(exit_code=0, stdout="", stderr="")

    async def run_python_script(
        self,
        *,
        source: str,
        working_dir: str | None = None,
        env: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> SandboxResult:
        self.calls.append(
            {"kind": "python", "source": source, "wd": working_dir, "env": dict(env or {})}
        )
        return SandboxResult(
            exit_code=self._script_exit_code, stdout="", stderr=self._script_stderr
        )

    async def write_files(self, *, files: dict[str, bytes], working_dir: str) -> None:
        self.calls.append(
            {"kind": "write_files", "wd": working_dir, "files": sorted(files)}
        )

    async def read_file(self, *, path: str, max_bytes: int) -> bytes:
        self.calls.append({"kind": "read_file", "path": path, "max_bytes": max_bytes})
        return self._artifact

    async def list_files(self, *, working_dir: str) -> list[str]:
        self.calls.append({"kind": "list_files", "wd": working_dir})
        return list(self._files)


class _RecordingStorage:
    def __init__(self) -> None:
        self.uploads: list[dict[str, Any]] = []

    async def upload(
        self,
        *,
        tenant_id: UUID,
        filename: str,
        data: bytes,
        content_type: str,
        ttl_seconds: int,
    ) -> UploadResult:
        self.uploads.append(
            {
                "tenant_id": str(tenant_id),
                "filename": filename,
                "size": len(data),
                "content_type": content_type,
                "ttl_seconds": ttl_seconds,
            }
        )
        return UploadResult(
            download_url=f"https://fake.invalid/{filename}",
            storage_key=f"tenants/{tenant_id}/x/{filename}",
            size_bytes=len(data),
            content_type=content_type,
        )


def _fake_skill(*, key: str = "pdf", runtime: SkillRuntime = SkillRuntime.python) -> Skill:
    skill = Skill()
    skill.id = uuid.uuid4()
    skill.key = key
    skill.name = "PDF Builder"
    skill.runtime = runtime
    skill.output_format = "pdf"
    skill.overview = "Build PDFs"
    skill.instructions = "Write to $HARNEX_OUTPUT_DIR"
    skill.scripts = {"helper.py": "print('hi')"}
    skill.metadata_ = {"mime_type": "application/pdf"}
    skill.embedding_model = "fake"
    skill.embedding_dim = 64
    skill.embedding = [0.0] * 64
    skill.content_hash = "deadbeef"
    return skill


def _mock_session(skill: Skill | None) -> Any:
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = skill
    session.execute = AsyncMock(return_value=exec_result)
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture()
def fakes() -> tuple[_RecordingRunner, _RecordingRunner, _RecordingStorage]:
    node_runner = _RecordingRunner(produces_files=["output.pdf"])
    py_runner = _RecordingRunner(produces_files=["output.pdf"])
    storage = _RecordingStorage()
    set_sandbox_runner(node_runner)
    set_python_sandbox_runner(py_runner)
    set_object_storage(storage)
    yield node_runner, py_runner, storage
    sbx._runner = None  # type: ignore[attr-defined]
    sbx._python_runner = None  # type: ignore[attr-defined]
    set_object_storage(None)  # type: ignore[arg-type]


async def test_python_skill_routes_to_python_runner_and_uploads(
    fakes: tuple[_RecordingRunner, _RecordingRunner, _RecordingStorage],
) -> None:
    node_runner, py_runner, storage = fakes
    session = _mock_session(_fake_skill(runtime=SkillRuntime.python))
    tenant_id = uuid.uuid4()

    outcome = await execute_skill(
        session,
        tenant_id=tenant_id,
        skill_key="pdf",
        code="print('hello pdf')",
    )

    assert outcome.status is ExecutionStatus.success
    assert outcome.skill_key == "pdf"
    assert outcome.runtime == "python"
    assert outcome.download_url == "https://fake.invalid/output.pdf"
    assert outcome.filename == "output.pdf"
    assert outcome.content_type == "application/pdf"

    # Python skills must not touch the Node sandbox.
    assert all(c["kind"] != "python" for c in node_runner.calls)
    py_kinds = [c["kind"] for c in py_runner.calls]
    assert "write_files" in py_kinds
    assert "python" in py_kinds
    assert "list_files" in py_kinds
    assert "read_file" in py_kinds

    assert storage.uploads == [
        {
            "tenant_id": str(tenant_id),
            "filename": "output.pdf",
            "size": len(b"%PDF-fake\n"),
            "content_type": "application/pdf",
            "ttl_seconds": 900,
        }
    ]
    session.add.assert_called_once()


async def test_node_skill_routes_to_node_runner(
    fakes: tuple[_RecordingRunner, _RecordingRunner, _RecordingStorage],
) -> None:
    node_runner, py_runner, _ = fakes
    session = _mock_session(_fake_skill(key="docx", runtime=SkillRuntime.node))

    outcome = await execute_skill(
        session,
        tenant_id=uuid.uuid4(),
        skill_key="docx",
        code="console.log('hi')",
    )
    assert outcome.status is ExecutionStatus.success
    assert outcome.runtime == "node"
    # Node runs `cd … && node -e …` via run_command, not run_python_script.
    assert all(c["kind"] != "python" for c in node_runner.calls)
    assert all(c["kind"] != "python" for c in py_runner.calls)


async def test_no_output_files_returns_structured_error(
    fakes: tuple[_RecordingRunner, _RecordingRunner, _RecordingStorage],
) -> None:
    _, _, storage = fakes
    # Override py runner to produce zero files.
    set_python_sandbox_runner(_RecordingRunner(produces_files=[]))
    session = _mock_session(_fake_skill())
    outcome = await execute_skill(
        session,
        tenant_id=uuid.uuid4(),
        skill_key="pdf",
        code="pass",
    )
    assert outcome.status is ExecutionStatus.error
    assert outcome.error_kind == "no_output"
    assert storage.uploads == []


async def test_unknown_skill_raises(
    fakes: tuple[_RecordingRunner, _RecordingRunner, _RecordingStorage],
) -> None:
    session = _mock_session(None)
    with pytest.raises(SkillNotFoundError):
        await execute_skill(
            session,
            tenant_id=uuid.uuid4(),
            skill_key="does-not-exist",
            code="pass",
        )
