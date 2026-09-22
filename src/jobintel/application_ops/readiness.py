from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from jobintel.application_ops.answer_bank import (
    build_answer_bank,
)


@dataclass(frozen=True)
class ReadinessCheck:
    key: str
    ok: bool
    blocking: bool
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


def build_readiness_checks(
    *,
    profile: Any,
    job: Any,
) -> list[ReadinessCheck]:
    answers = build_answer_bank(
        profile,
        company=getattr(
            job,
            "company",
            None,
        ),
        title=getattr(
            job,
            "title",
            None,
        ),
    )

    checks: list[ReadinessCheck] = []

    for key, label in (
        (
            "full_name",
            "Candidate name",
        ),
        (
            "email",
            "Email",
        ),
        (
            "phone",
            "Phone",
        ),
    ):
        value = answers[key].value
        checks.append(
            ReadinessCheck(
                key=key,
                ok=bool(value),
                blocking=True,
                message=(f"{label} is available." if value else f"{label} is missing."),
            )
        )

    apply_url = getattr(
        job,
        "apply_url",
        None,
    )

    checks.append(
        ReadinessCheck(
            key="apply_url",
            ok=bool(apply_url),
            blocking=True,
            message=(
                "Application URL is available."
                if apply_url
                else "Application URL is missing."
            ),
        )
    )

    resume_filename = getattr(
        profile,
        "source_resume_filename",
        None,
    )

    checks.append(
        ReadinessCheck(
            key="resume_profile_source",
            ok=bool(resume_filename),
            blocking=False,
            message=(
                "Profile is linked to a parsed resume."
                if resume_filename
                else (
                    "No source resume filename is stored; "
                    "manual resume review is recommended."
                )
            ),
        )
    )

    notice = answers["notice_period_days"].value

    checks.append(
        ReadinessCheck(
            key="notice_period_days",
            ok=notice is not None,
            blocking=False,
            message=(
                "Notice period is available."
                if notice is not None
                else "Notice period needs review."
            ),
        )
    )

    return checks


def readiness_payload(
    *,
    profile: Any,
    job: Any,
) -> dict:
    checks = build_readiness_checks(
        profile=profile,
        job=job,
    )

    blockers = [check.message for check in checks if (check.blocking and not check.ok)]

    return {
        "ready_for_review": (len(blockers) == 0),
        "auto_submit_allowed": False,
        "blocking_issues": blockers,
        "checks": [check.to_dict() for check in checks],
    }
