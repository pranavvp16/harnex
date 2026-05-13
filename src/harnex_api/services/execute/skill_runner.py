"""Execute a built-in skill: run agent-supplied code in the Blaxel sandbox, capture the file."""

from __future__ import annotations

import mimetypes
import time
import uuid
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.config import get_settings
from harnex_api.db.models import Execution, ExecutionMode, ExecutionStatus, Skill, SkillRuntime
from harnex_api.db.session import session_scope
from harnex_api.logging import get_logger
from harnex_api.services.execute.sandbox import (
    SandboxResult,
    get_python_sandbox_runner,
    get_sandbox_runner,
)
from harnex_api.services.object_storage import UploadResult, get_object_storage
from harnex_api.services.usage.monthly import bump_usage_monthly

_log = get_logger(__name__)


class SkillNotFoundError(LookupError):
    pass


@dataclass
class SkillOutcome:
    status: ExecutionStatus
    skill_key: str
    runtime: str
    output_format: str
    download_url: str | None = None
    filename: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    duration_ms: int | None = None
    error_kind: str | None = None
    error_message: str | None = None
    execution_id: str | None = None


def _content_type_for(skill: Skill, filename: str) -> str:
    declared = skill.metadata_.get("mime_type") if isinstance(skill.metadata_, dict) else None
    if isinstance(declared, str) and declared:
        return declared
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


async def _record_skill_execution(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    api_key_id: UUID | None,
    skill: Skill,
    outcome: SkillOutcome,
    upload: UploadResult | None,
) -> Execution:
    row = Execution(
        tenant_id=tenant_id,
        connection_id=None,
        api_key_id=api_key_id,
        mode=ExecutionMode.skill,
        status=outcome.status,
        operation_id=f"skill:{skill.key}",
        request_summary={"skill_key": skill.key, "runtime": skill.runtime.value},
        response_summary=(
            {
                "download_url": upload.download_url,
                "storage_key": upload.storage_key,
                "filename": outcome.filename,
                "content_type": outcome.content_type,
                "size_bytes": outcome.size_bytes,
            }
            if upload is not None
            else {}
        ),
        error_kind=outcome.error_kind,
        error_message=outcome.error_message,
        duration_ms=outcome.duration_ms,
        artifact_url=upload.download_url if upload is not None else None,
        artifact_bytes=upload.size_bytes if upload is not None else None,
    )
    session.add(row)
    await session.flush()
    outcome.execution_id = str(row.id)
    try:
        async with session_scope() as usage_session:
            await bump_usage_monthly(usage_session, tenant_id, executions=1)
    except Exception:
        _log.exception("usage bump failed — ignoring", tenant_id=str(tenant_id))
    return row


async def execute_skill(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    skill_key: str,
    code: str,
    api_key_id: UUID | None = None,
) -> SkillOutcome:
    """Run an agent-supplied script for a built-in skill and ship the output file.

    Flow:
        1. Look up the skill by key.
        2. Allocate a per-execution working dir on the sandbox.
        3. Stage the skill's helper scripts (if any) into the working dir.
        4. Run the agent's code in the matching runtime, with HARNEX_OUTPUT_DIR
           pointed at ``<working_dir>/out``.
        5. Read the first file the script produced in that dir.
        6. Upload to object storage; record an Execution row; return the
           signed download URL.
    """
    settings = get_settings()
    skill = (
        await session.execute(select(Skill).where(Skill.key == skill_key))
    ).scalar_one_or_none()
    if skill is None:
        raise SkillNotFoundError(skill_key)

    exec_id = uuid.uuid4().hex
    working_dir = f"/tmp/harnex/{exec_id}"
    output_dir = f"{working_dir}/out"
    runner = (
        get_python_sandbox_runner() if skill.runtime is SkillRuntime.python
        else get_sandbox_runner()
    )
    started = time.perf_counter()

    try:
        script_files: dict[str, bytes] = {
            name: content.encode("utf-8") if isinstance(content, str) else bytes(content)
            for name, content in (skill.scripts or {}).items()
        }
        await runner.write_files(files=script_files, working_dir=working_dir)
        # Ensure the output directory exists before the script runs — most
        # skill templates also call mkdir but doing it here is cheap insurance.
        await runner.run_command(command=f"mkdir -p {output_dir}")

        env = {"HARNEX_OUTPUT_DIR": output_dir}
        if skill.runtime is SkillRuntime.node:
            # Node runs eval-mode through run_node_script today; pass env via a
            # wrapper command so HARNEX_OUTPUT_DIR is visible to the script.
            wrapped = (
                f"export HARNEX_OUTPUT_DIR={output_dir} && cd {working_dir} && "
                f"node -e \"{_node_inline_program(code)}\""
            )
            result: SandboxResult = await runner.run_command(
                command=wrapped, timeout_seconds=settings.skill_execute_timeout_seconds
            )
        else:
            result = await runner.run_python_script(
                source=code,
                working_dir=working_dir,
                env=env,
                timeout_seconds=settings.skill_execute_timeout_seconds,
            )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        outcome = SkillOutcome(
            status=ExecutionStatus.error,
            skill_key=skill.key,
            runtime=skill.runtime.value,
            output_format=skill.output_format,
            error_kind="sandbox_error",
            error_message=str(exc)[:2048],
            duration_ms=duration_ms,
        )
        await _record_skill_execution(
            session, tenant_id=tenant_id, api_key_id=api_key_id,
            skill=skill, outcome=outcome, upload=None,
        )
        return outcome

    duration_ms = int((time.perf_counter() - started) * 1000)

    if result.exit_code != 0:
        outcome = SkillOutcome(
            status=ExecutionStatus.error,
            skill_key=skill.key,
            runtime=skill.runtime.value,
            output_format=skill.output_format,
            error_kind="script_error",
            error_message=(result.stderr or result.stdout)[:2048],
            duration_ms=duration_ms,
        )
        await _record_skill_execution(
            session, tenant_id=tenant_id, api_key_id=api_key_id,
            skill=skill, outcome=outcome, upload=None,
        )
        return outcome

    files = await runner.list_files(working_dir=output_dir)
    if not files:
        outcome = SkillOutcome(
            status=ExecutionStatus.error,
            skill_key=skill.key,
            runtime=skill.runtime.value,
            output_format=skill.output_format,
            error_kind="no_output",
            error_message=(
                f"script produced no files in {output_dir}; "
                "skills must write their artifact under $HARNEX_OUTPUT_DIR"
            ),
            duration_ms=duration_ms,
        )
        await _record_skill_execution(
            session, tenant_id=tenant_id, api_key_id=api_key_id,
            skill=skill, outcome=outcome, upload=None,
        )
        return outcome

    filename = files[0]
    artifact_path = f"{output_dir}/{filename}"
    max_bytes = settings.skill_max_artifact_bytes
    try:
        data = await runner.read_file(path=artifact_path, max_bytes=max_bytes)
    except RuntimeError as exc:
        outcome = SkillOutcome(
            status=ExecutionStatus.error,
            skill_key=skill.key,
            runtime=skill.runtime.value,
            output_format=skill.output_format,
            error_kind="artifact_too_large",
            error_message=str(exc),
            duration_ms=duration_ms,
        )
        await _record_skill_execution(
            session, tenant_id=tenant_id, api_key_id=api_key_id,
            skill=skill, outcome=outcome, upload=None,
        )
        return outcome

    content_type = _content_type_for(skill, filename)
    storage = get_object_storage()
    upload = await storage.upload(
        tenant_id=tenant_id,
        filename=filename,
        data=data,
        content_type=content_type,
        ttl_seconds=settings.skill_download_url_ttl_seconds,
    )

    outcome = SkillOutcome(
        status=ExecutionStatus.success,
        skill_key=skill.key,
        runtime=skill.runtime.value,
        output_format=skill.output_format,
        download_url=upload.download_url,
        filename=filename,
        content_type=content_type,
        size_bytes=upload.size_bytes,
        duration_ms=duration_ms,
    )
    await _record_skill_execution(
        session, tenant_id=tenant_id, api_key_id=api_key_id,
        skill=skill, outcome=outcome, upload=upload,
    )
    return outcome


def _node_inline_program(code: str) -> str:
    """Encode ``code`` so it can be passed to ``node -e "..."`` via double quotes.

    Matches the trick in :func:`BlaxelSandboxRunner.run_node_script` but exposed
    here because the skill path wraps the invocation in a ``cd`` + ``export``
    shell pipeline.
    """
    import base64

    encoded = base64.b64encode(code.encode("utf-8")).decode("ascii")
    return f'eval(Buffer.from(\\"{encoded}\\", \\"base64\\").toString(\\"utf-8\\"))'


def _ensure_outcome_envelope(outcome: SkillOutcome) -> dict[str, Any]:
    """Public-shaped dict the MCP tool returns."""
    return {
        "status": outcome.status.value,
        "skill_key": outcome.skill_key,
        "runtime": outcome.runtime,
        "output_format": outcome.output_format,
        "download_url": outcome.download_url,
        "filename": outcome.filename,
        "content_type": outcome.content_type,
        "size_bytes": outcome.size_bytes,
        "duration_ms": outcome.duration_ms,
        "error_kind": outcome.error_kind,
        "error_message": outcome.error_message,
        "execution_id": outcome.execution_id,
    }


__all__ = [
    "SkillNotFoundError",
    "SkillOutcome",
    "_ensure_outcome_envelope",
    "execute_skill",
]
