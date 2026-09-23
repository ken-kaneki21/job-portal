from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class ApplicationEventLike(Protocol):
    id: int
    new_status: str
    created_at: datetime


@dataclass(frozen=True)
class HistoricalOutcome:
    outcome: str
    value: float
    positive: bool
    applied_at: datetime
    ever_interviewed: bool


def _event_sort_key(
    event: ApplicationEventLike,
) -> tuple[datetime, int]:
    return (
        event.created_at,
        event.id,
    )


def derive_historical_outcome(
    events: Iterable[ApplicationEventLike],
) -> HistoricalOutcome | None:
    ordered = sorted(
        list(events),
        key=_event_sort_key,
    )

    applied_event = next(
        (event for event in ordered if event.new_status.strip().lower() == "applied"),
        None,
    )

    if applied_event is None:
        return None

    applied_at = applied_event.created_at

    post_application = [event for event in ordered if event.created_at >= applied_at]

    statuses = [event.new_status.strip().lower() for event in post_application]

    if "offer" in statuses:
        return HistoricalOutcome(
            outcome="offer",
            value=2.0,
            positive=True,
            applied_at=applied_at,
            ever_interviewed=True,
        )

    ever_interviewed = "interviewing" in statuses

    if ever_interviewed:
        return HistoricalOutcome(
            outcome="interviewing",
            value=1.0,
            positive=True,
            applied_at=applied_at,
            ever_interviewed=True,
        )

    if "rejected" in statuses:
        return HistoricalOutcome(
            outcome="rejected",
            value=-1.0,
            positive=False,
            applied_at=applied_at,
            ever_interviewed=False,
        )

    return None
