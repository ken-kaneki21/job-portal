from __future__ import annotations

CANONICAL_STATUSES = {
    "new",
    "seen",
    "saved",
    "dismissed",
    "applied",
    "interviewing",
    "rejected",
    "offer",
}

STATUS_ALIASES = {
    "reviewed": "seen",
    "skipped": "dismissed",
    "interview": "interviewing",
}

TERMINAL_STATUSES = {
    "rejected",
    "offer",
}

ACTIVE_APPLICATION_STATUSES = {
    "applied",
    "interviewing",
    "offer",
}


def normalize_status(value: str) -> str:
    normalized = value.strip().lower()

    normalized = STATUS_ALIASES.get(
        normalized,
        normalized,
    )

    if normalized not in CANONICAL_STATUSES:
        allowed = ", ".join(sorted(CANONICAL_STATUSES))
        raise ValueError(f"Invalid application status: {value}. Allowed: {allowed}")

    return normalized


def is_completed_outcome(
    value: str,
) -> bool:
    return normalize_status(value) in {
        "interviewing",
        "rejected",
        "offer",
    }


def transition_note(
    previous: str | None,
    new: str,
) -> str | None:
    if previous is None:
        return None

    previous_status = normalize_status(previous)
    new_status = normalize_status(new)

    if previous_status == new_status:
        return "Status is unchanged."

    if previous_status in TERMINAL_STATUSES and new_status not in TERMINAL_STATUSES:
        return "Reopening a previously completed application outcome."

    return None
