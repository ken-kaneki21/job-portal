from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HistoricalOutcome:
    outcome: str
    value: float
    positive: bool
    applied_at: datetime
    ever_interviewed: bool


def _event_sort_key(event) -> tuple:
    return (
        getattr(event, "created_at", None),
        getattr(event, "id", 0),
    )


def derive_historical_outcome(
    events: Iterable[object],
) -> HistoricalOutcome | None:
    ordered = sorted(
        list(events),
        key=_event_sort_key,
    )

    applied_event = next(
        (
            event
            for event in ordered
            if str(getattr(event, "new_status", "")).strip().lower() == "applied"
        ),
        None,
    )

    if applied_event is None:
        return None

    applied_at = getattr(
        applied_event,
        "created_at",
        None,
    )

    if applied_at is None:
        return None

    post_application = [
        event
        for event in ordered
        if getattr(event, "created_at", None) is not None
        and event.created_at >= applied_at
    ]

    statuses = [
        str(getattr(event, "new_status", "")).strip().lower()
        for event in post_application
    ]

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
