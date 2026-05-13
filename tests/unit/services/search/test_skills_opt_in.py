"""SearchService honors the ``include_skills`` opt-in flag."""

from __future__ import annotations

import pytest

from harnex_api.services.search.embeddings import FakeEmbeddingProvider
from harnex_api.services.search.service import SearchService
from harnex_api.services.search.vector_search import (
    FakeSkillVectorSearch,
    FakeVectorSearch,
)


@pytest.fixture()
def skill_search() -> FakeSkillVectorSearch:
    search = FakeSkillVectorSearch()
    embedder = FakeEmbeddingProvider(dim=64)

    async def _seed() -> None:
        for key, output_format, overview in [
            ("pdf", "pdf", "Build PDF documents and printable reports"),
            ("docx", "docx", "Build Microsoft Word documents and memos"),
            ("xlsx", "xlsx", "Build Excel spreadsheets with formulas"),
            ("pptx", "pptx", "Build PowerPoint slide decks"),
        ]:
            result = await embedder.embed(f"{key} ({output_format}) — {overview}")
            search.register(
                skill_key=key,
                name=key.upper(),
                runtime="python",
                output_format=output_format,
                instructions=f"# {key}\nWrite output to $HARNEX_OUTPUT_DIR",
                embedding=result.vector,
            )

    import asyncio

    asyncio.get_event_loop().run_until_complete(_seed())
    yield search
    search.reset()


async def test_default_search_does_not_return_skills(
    skill_search: FakeSkillVectorSearch,
) -> None:
    svc = SearchService(
        embeddings=FakeEmbeddingProvider(dim=64),
        vector_search=FakeVectorSearch(),
        skill_search=skill_search,
    )
    result = await svc.search(tenant_id="t1", query="build a pdf report")
    assert result.skills == []


async def test_skills_opt_in_returns_top_skill(
    skill_search: FakeSkillVectorSearch,
) -> None:
    svc = SearchService(
        embeddings=FakeEmbeddingProvider(dim=64),
        vector_search=FakeVectorSearch(),
        skill_search=skill_search,
    )
    result = await svc.search(
        tenant_id="t1",
        query="build a pdf report with quarterly numbers",
        include_skills=True,
    )
    assert len(result.skills) == 1
    top = result.skills[0]
    assert top.skill_key == "pdf"
    assert "HARNEX_OUTPUT_DIR" in top.instructions


async def test_skills_opt_in_picks_xlsx_for_spreadsheet_query(
    skill_search: FakeSkillVectorSearch,
) -> None:
    svc = SearchService(
        embeddings=FakeEmbeddingProvider(dim=64),
        vector_search=FakeVectorSearch(),
        skill_search=skill_search,
    )
    result = await svc.search(
        tenant_id="t1",
        query="export the customer list as an excel spreadsheet",
        include_skills=True,
    )
    assert result.skills[0].skill_key == "xlsx"


async def test_skills_opt_in_suppresses_api_hits(
    skill_search: FakeSkillVectorSearch,
) -> None:
    """``include_skills=True`` is exclusive — API hits / clarification are dropped."""

    class _NoisyVectorSearch(FakeVectorSearch):
        async def search(self, **_: object) -> list:  # type: ignore[override]
            raise AssertionError("API search must not run when include_skills=True")

    svc = SearchService(
        embeddings=FakeEmbeddingProvider(dim=64),
        vector_search=_NoisyVectorSearch(),
        skill_search=skill_search,
    )
    result = await svc.search(
        tenant_id="t1",
        query="build a pdf report",
        include_skills=True,
    )
    assert result.hits == []
    assert result.clarification_needed is False
    assert result.candidate_connectors == []
    assert len(result.skills) == 1
    assert result.skills[0].skill_key == "pdf"
