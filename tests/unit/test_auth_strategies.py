from __future__ import annotations

import pytest

from harnex_api.auth.strategies import AuthCredentials, get_strategy
from harnex_api.db.models import AuthFlow


def test_api_key_header_strategy():
    strat = get_strategy(AuthFlow.api_key_header)
    ctx = strat.build(
        {"header_name": "X-Token", "prefix": "tok_"},
        AuthCredentials(flow=AuthFlow.api_key_header, values={"api_key": "abc"}),
    )
    assert ctx.headers == {"X-Token": "tok_abc"}
    assert ctx.basic_auth is None


def test_bearer_strategy():
    ctx = get_strategy(AuthFlow.bearer).build(
        {}, AuthCredentials(flow=AuthFlow.bearer, values={"token": "xyz"})
    )
    assert ctx.headers == {"Authorization": "Bearer xyz"}


def test_basic_strategy():
    ctx = get_strategy(AuthFlow.basic).build(
        {},
        AuthCredentials(flow=AuthFlow.basic, values={"username": "u", "password": "p"}),
    )
    assert ctx.basic_auth == ("u", "p")
    assert ctx.headers == {}


def test_none_strategy():
    ctx = get_strategy(AuthFlow.none).build({}, AuthCredentials(flow=AuthFlow.none, values={}))
    assert ctx.headers == {}
    assert ctx.query == {}


def test_unknown_flow_raises():
    with pytest.raises(ValueError):
        get_strategy("not-a-flow")  # type: ignore[arg-type]
