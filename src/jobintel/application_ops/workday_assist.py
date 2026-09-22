from __future__ import annotations

from dataclasses import asdict, dataclass

from jobintel.application_ops.answer_bank import (
    ApplicationAnswer,
)

FIELD_LABELS: dict[
    str,
    tuple[str, ...],
] = {
    "first_name": (
        "first name",
        "given name",
    ),
    "last_name": (
        "last name",
        "family name",
        "surname",
    ),
    "email": (
        "email",
        "email address",
    ),
    "phone": (
        "phone",
        "phone number",
        "mobile",
        "mobile number",
    ),
    "current_location": (
        "location",
        "current location",
        "city",
    ),
    "linkedin_url": (
        "linkedin",
        "linkedin profile",
        "linkedin url",
    ),
    "github_url": (
        "github",
        "github profile",
        "github url",
    ),
    "portfolio_url": (
        "portfolio",
        "website",
        "personal website",
    ),
    "current_company": (
        "current company",
        "company",
        "employer",
    ),
    "current_title": (
        "current title",
        "job title",
        "current job title",
    ),
    "total_experience_years": (
        "years of experience",
        "total experience",
        "total years of experience",
    ),
    "notice_period_days": (
        "notice period",
        "notice period in days",
        "days notice",
    ),
    "expected_compensation": (
        "expected compensation",
        "expected salary",
        "salary expectation",
        "expected ctc",
    ),
}


@dataclass(frozen=True)
class WorkdaySuggestion:
    key: str
    labels: tuple[str, ...]
    value: str | int | float | None
    sensitive: bool
    review_required: bool

    def to_dict(self) -> dict:
        return asdict(self)


def build_workday_suggestions(
    answers: dict[
        str,
        ApplicationAnswer,
    ],
) -> list[WorkdaySuggestion]:
    suggestions: list[WorkdaySuggestion] = []

    for key, labels in FIELD_LABELS.items():
        answer = answers.get(key)

        if answer is None:
            continue

        suggestions.append(
            WorkdaySuggestion(
                key=key,
                labels=labels,
                value=answer.value,
                sensitive=answer.sensitive,
                review_required=(answer.review_required),
            )
        )

    return suggestions
