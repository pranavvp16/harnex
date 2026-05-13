"""Unit coverage for ``discover_builtins`` — the pure-IO half of the seeder.

The DB upsert path is exercised via integration tests; here we just verify the
filesystem walk loads the four vendored skills, computes a deterministic
content hash, and constructs an ``embedding_text`` that an embedding model can
plausibly latch onto.
"""

from __future__ import annotations

from harnex_api.db.models import SkillRuntime
from harnex_api.services.skills.registry import discover_builtins


def test_discover_builtins_loads_four_skills() -> None:
    loaded = discover_builtins()
    by_key = {s.key: s for s in loaded}
    assert set(by_key) == {"docx", "pdf", "pptx", "xlsx"}


def test_discover_builtins_runtimes_and_formats() -> None:
    by_key = {s.key: s for s in discover_builtins()}
    # docx ships docx-js → Node; the rest are Python libs (reportlab/openpyxl/python-pptx).
    assert by_key["docx"].runtime is SkillRuntime.node
    assert by_key["docx"].output_format == "docx"
    assert by_key["pdf"].runtime is SkillRuntime.python
    assert by_key["pdf"].output_format == "pdf"
    assert by_key["xlsx"].runtime is SkillRuntime.python
    assert by_key["xlsx"].output_format == "xlsx"
    assert by_key["pptx"].runtime is SkillRuntime.python
    assert by_key["pptx"].output_format == "pptx"


def test_content_hash_is_deterministic() -> None:
    first = {s.key: s.content_hash for s in discover_builtins()}
    second = {s.key: s.content_hash for s in discover_builtins()}
    assert first == second


def test_instructions_carry_skill_md_body() -> None:
    by_key = {s.key: s for s in discover_builtins()}
    # The agent uses these instructions to write code — minimal smoke check that
    # we're shipping more than the manifest. Each SKILL.md is comfortably > 200 chars.
    for skill in by_key.values():
        assert len(skill.instructions) > 200, skill.key
        assert "HARNEX_OUTPUT_DIR" in skill.instructions, skill.key


def test_embedding_text_contains_format_and_overview() -> None:
    by_key = {s.key: s for s in discover_builtins()}
    for skill in by_key.values():
        text = skill.embedding_text
        assert skill.output_format in text, skill.key
        # The overview is the document-intent anchor; the first ~30 chars of it
        # should appear verbatim in the embedding text.
        assert skill.overview[:30] in text, skill.key


def test_support_files_loaded_into_scripts_dict() -> None:
    """Top-level helper files (forms.md, ooxml.md, recalc.py, html2pptx.md) and
    ``scripts/`` subtrees vendored from composio are now picked up by the
    registry walk — they were silently dropped when ``_load_one`` only read
    ``scripts/``. Tests guard against regressing back to that behavior.
    """
    by_key = {s.key: s for s in discover_builtins()}

    # composio's pdf skill ships forms.md + reference.md alongside SKILL.md.
    assert "forms.md" in by_key["pdf"].scripts
    assert "reference.md" in by_key["pdf"].scripts
    assert "scripts/check_fillable_fields.py" in by_key["pdf"].scripts

    # docx ships docx-js.md + ooxml.md at the top level plus a python helpers tree.
    assert "docx-js.md" in by_key["docx"].scripts
    assert "ooxml.md" in by_key["docx"].scripts
    assert "scripts/document.py" in by_key["docx"].scripts

    # xlsx ships a single recalc.py utility at the top level.
    assert "recalc.py" in by_key["xlsx"].scripts

    # pptx ships html2pptx.md + ooxml.md plus several scripts.
    assert "html2pptx.md" in by_key["pptx"].scripts
    assert "scripts/html2pptx.js" in by_key["pptx"].scripts


def test_license_and_manifest_excluded_from_scripts() -> None:
    """Manifest + LICENSE files must not leak into the script payload; they
    aren't authoring guidance and would inflate the search response by KB.
    """
    for skill in discover_builtins():
        assert "skill.yaml" not in skill.scripts, skill.key
        assert "LICENSE.txt" not in skill.scripts, skill.key
        assert "SKILL.md" not in skill.scripts, skill.key
