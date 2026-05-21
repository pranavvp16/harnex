from __future__ import annotations

from harnex_api.api.schemas.common import ApiModel


class UsageCurrent(ApiModel):
    year_month: str
    executions: int
    searches: int
    embedding_tokens: int
    monthly_execution_quota: int


class DailyExecutionPoint(ApiModel):
    date: str  # YYYY-MM-DD (UTC)
    count: int


class DailyExecutions(ApiModel):
    days: int
    points: list[DailyExecutionPoint]


__all__ = ["DailyExecutionPoint", "DailyExecutions", "UsageCurrent"]
