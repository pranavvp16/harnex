"""Idempotent seeder for built-in skills.

Walks ``src/harnex_api/skills/builtins/<key>/`` and upserts a row in the
``skills`` table for each one. Only re-embeds when the content hash changes,
so restarts are cheap. Mirrors :func:`harnex_api.connectors.registry.register_builtins`
in spirit — pure import-time work plus a single DB pass.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from harnex_api.db.models import Skill, SkillRuntime
from harnex_api.logging import get_logger
from harnex_api.services.search.embeddings import EmbeddingProvider, get_embedding_provider

_BUILTINS_DIR = Path(__file__).resolve().parents[2] / "skills" / "builtins"
_log = get_logger(__name__)


@dataclass(frozen=True)
class _LoadedSkill:
    key: str
    name: str
    runtime: SkillRuntime
    output_format: str
    overview: str
    instructions: str
    scripts: dict[str, str]
    metadata: dict[str, Any]
    content_hash: str

    @property
    def embedding_text(self) -> str:
        # The overview is the document-intent anchor; format gets repeated so
        # "pdf"/"xlsx"/"docx"/"pptx" tokens stand out for keyword tsv.
        return f"{self.name} ({self.output_format}) — {self.overview}"


def _load_one(folder: Path) -> _LoadedSkill:
    manifest_path = folder / "skill.yaml"
    skill_md_path = folder / "SKILL.md"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"missing skill.yaml in {folder}")
    if not skill_md_path.is_file():
        raise FileNotFoundError(f"missing SKILL.md in {folder}")
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    instructions = skill_md_path.read_text(encoding="utf-8")

    scripts: dict[str, str] = {}
    scripts_dir = folder / "scripts"
    if scripts_dir.is_dir():
        for child in sorted(scripts_dir.rglob("*")):
            if child.is_file():
                rel = str(child.relative_to(scripts_dir))
                scripts[rel] = child.read_text(encoding="utf-8")

    key = str(manifest["key"])
    name = str(manifest["name"])
    runtime = SkillRuntime(str(manifest["runtime"]))
    output_format = str(manifest["output_format"])
    overview = str(manifest["overview"]).strip()
    metadata = dict(manifest.get("metadata", {}))

    hasher = hashlib.sha256()
    hasher.update(name.encode("utf-8"))
    hasher.update(runtime.value.encode("utf-8"))
    hasher.update(output_format.encode("utf-8"))
    hasher.update(overview.encode("utf-8"))
    hasher.update(instructions.encode("utf-8"))
    hasher.update(json.dumps(scripts, sort_keys=True).encode("utf-8"))
    hasher.update(json.dumps(metadata, sort_keys=True).encode("utf-8"))
    content_hash = hasher.hexdigest()

    return _LoadedSkill(
        key=key,
        name=name,
        runtime=runtime,
        output_format=output_format,
        overview=overview,
        instructions=instructions,
        scripts=scripts,
        metadata=metadata,
        content_hash=content_hash,
    )


def discover_builtins(root: Path | None = None) -> list[_LoadedSkill]:
    """Read every ``<root>/<key>/`` subdir into a ``_LoadedSkill``."""
    base = root or _BUILTINS_DIR
    if not base.is_dir():
        return []
    out: list[_LoadedSkill] = []
    for child in sorted(base.iterdir()):
        if not child.is_dir():
            continue
        out.append(_load_one(child))
    return out


async def seed_builtin_skills(
    session: AsyncSession,
    *,
    embeddings: EmbeddingProvider | None = None,
    root: Path | None = None,
) -> int:
    """Insert/update skill rows. Returns the number of rows that changed.

    Idempotent — when ``content_hash`` matches the existing row, we skip the
    embedding call entirely.
    """
    provider = embeddings or get_embedding_provider()
    loaded = discover_builtins(root)
    if not loaded:
        _log.info("skills_seed_empty", builtins_dir=str(root or _BUILTINS_DIR))
        return 0

    existing_rows = (await session.execute(select(Skill))).scalars().all()
    by_key: dict[str, Skill] = {row.key: row for row in existing_rows}

    needs_embedding: list[_LoadedSkill] = []
    for skill in loaded:
        existing = by_key.get(skill.key)
        if existing is None or existing.content_hash != skill.content_hash:
            needs_embedding.append(skill)

    if not needs_embedding:
        _log.info("skills_seed_noop", count=len(loaded))
        return 0

    vectors, _tokens = await provider.embed_batch([s.embedding_text for s in needs_embedding])
    changed = 0
    for skill, vector in zip(needs_embedding, vectors, strict=True):
        existing = by_key.get(skill.key)
        if existing is None:
            session.add(
                Skill(
                    key=skill.key,
                    name=skill.name,
                    runtime=skill.runtime,
                    output_format=skill.output_format,
                    overview=skill.overview,
                    instructions=skill.instructions,
                    scripts=skill.scripts,
                    metadata_=skill.metadata,
                    embedding_model=provider.model_name,
                    embedding_dim=provider.dim,
                    embedding=vector,
                    content_hash=skill.content_hash,
                )
            )
        else:
            existing.name = skill.name
            existing.runtime = skill.runtime
            existing.output_format = skill.output_format
            existing.overview = skill.overview
            existing.instructions = skill.instructions
            existing.scripts = skill.scripts
            existing.metadata_ = skill.metadata
            existing.embedding_model = provider.model_name
            existing.embedding_dim = provider.dim
            existing.embedding = vector
            existing.content_hash = skill.content_hash
        changed += 1

    await session.commit()
    _log.info("skills_seeded", changed=changed, total=len(loaded))
    return changed


__all__ = ["discover_builtins", "seed_builtin_skills"]
