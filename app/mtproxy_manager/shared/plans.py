from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SubscriptionPlan:
    code: str
    title: str
    duration_days: int


PLANS = {
    "1m": SubscriptionPlan(code="1m", title="1 месяц", duration_days=30),
    "3m": SubscriptionPlan(code="3m", title="3 месяца", duration_days=90),
    "1y": SubscriptionPlan(code="1y", title="1 год", duration_days=365),
}


def get_plan(code: str) -> SubscriptionPlan:
    try:
        return PLANS[code]
    except KeyError as exc:
        raise ValueError(f"Unknown plan code: {code}") from exc
