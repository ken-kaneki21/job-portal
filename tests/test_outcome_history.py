from datetime import (
    UTC,
    datetime,
    timedelta,
)
from types import SimpleNamespace

from jobintel.outcome_learning.history import (
    derive_historical_outcome,
)


def event(
    event_id: int,
    status: str,
    at: datetime,
):
    return SimpleNamespace(
        id=event_id,
        new_status=status,
        created_at=at,
    )


def test_rejected_after_interview_remains_positive_interview_signal():
    base = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    outcome = derive_historical_outcome(
        [
            event(1, "applied", base),
            event(2, "interviewing", base + timedelta(days=3)),
            event(3, "rejected", base + timedelta(days=10)),
        ]
    )

    assert outcome is not None
    assert outcome.outcome == "interviewing"
    assert outcome.value == 1.0
    assert outcome.positive is True
    assert outcome.ever_interviewed is True
    assert outcome.applied_at == base


def test_offer_is_strongest_positive_signal():
    base = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    outcome = derive_historical_outcome(
        [
            event(1, "applied", base),
            event(2, "interviewing", base + timedelta(days=2)),
            event(3, "offer", base + timedelta(days=8)),
        ]
    )

    assert outcome is not None
    assert outcome.outcome == "offer"
    assert outcome.value == 2.0
    assert outcome.positive is True
    assert outcome.ever_interviewed is True


def test_rejection_without_interview_is_negative():
    base = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    outcome = derive_historical_outcome(
        [
            event(1, "applied", base),
            event(2, "rejected", base + timedelta(days=4)),
        ]
    )

    assert outcome is not None
    assert outcome.outcome == "rejected"
    assert outcome.value == -1.0
    assert outcome.positive is False
    assert outcome.ever_interviewed is False


def test_history_without_applied_event_is_excluded():
    base = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    outcome = derive_historical_outcome(
        [
            event(1, "interviewing", base),
            event(2, "rejected", base + timedelta(days=3)),
        ]
    )

    assert outcome is None


def test_incomplete_application_has_no_training_outcome():
    base = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    outcome = derive_historical_outcome(
        [
            event(1, "applied", base),
        ]
    )

    assert outcome is None
