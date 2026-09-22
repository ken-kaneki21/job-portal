import pytest

from jobintel.application_ops.status import (
    is_completed_outcome,
    normalize_status,
    transition_note,
)


def test_normalize_canonical_status():
    assert normalize_status(" applied ") == "applied"


def test_normalize_legacy_aliases():
    assert normalize_status("reviewed") == "seen"
    assert normalize_status("skipped") == "dismissed"
    assert normalize_status("interview") == "interviewing"


def test_invalid_status_rejected():
    with pytest.raises(ValueError):
        normalize_status("maybe")


def test_completed_outcomes():
    assert is_completed_outcome("interviewing")
    assert is_completed_outcome("rejected")
    assert is_completed_outcome("offer")
    assert not is_completed_outcome("applied")


def test_reopen_note():
    assert transition_note(
        "rejected",
        "applied",
    )
