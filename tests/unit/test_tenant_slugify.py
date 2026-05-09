from __future__ import annotations

from harnex_api.services.tenant.create import slugify


def test_slugify_basic() -> None:
    assert slugify("Acme AI Lab") == "acme-ai-lab"


def test_slugify_strips_punctuation_and_collapses_runs() -> None:
    assert slugify("  Foo, Bar!! Baz??  ") == "foo-bar-baz"


def test_slugify_empty_input_falls_back() -> None:
    assert slugify("") == "workspace"
    assert slugify("$#@") == "workspace"


def test_slugify_truncates_long_names() -> None:
    out = slugify("x" * 200)
    assert len(out) <= 48
    assert out == "x" * 48
