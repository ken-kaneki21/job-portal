from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ApplicationAnswer:
    key: str
    value: str | int | float | None
    source: str
    sensitive: bool = False
    review_required: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _text(
    value: Any,
) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    return text or None


def _latest_experience(
    profile: Any,
) -> Any | None:
    experiences = list(
        getattr(
            profile,
            "experience",
            [],
        )
        or []
    )

    if not experiences:
        return None

    for item in experiences:
        end_date = _text(
            getattr(
                item,
                "end_date",
                None,
            )
        )

        if end_date and end_date.lower() in {
            "present",
            "current",
            "now",
        }:
            return item

    return experiences[0]


def build_answer_bank(
    profile: Any,
    *,
    company: str | None = None,
    title: str | None = None,
) -> dict[str, ApplicationAnswer]:
    identity = getattr(
        profile,
        "identity",
        None,
    )
    preferences = getattr(
        profile,
        "preferences",
        None,
    )
    latest = _latest_experience(profile)

    full_name = _text(
        getattr(
            identity,
            "full_name",
            None,
        )
    )

    first_name = None
    last_name = None

    if full_name:
        parts = full_name.split()
        first_name = parts[0]
        if len(parts) > 1:
            last_name = " ".join(parts[1:])

    company_name = company or (
        _text(
            getattr(
                latest,
                "company",
                None,
            )
        )
    )

    role_name = title or (
        _text(
            getattr(
                latest,
                "title",
                None,
            )
        )
    )

    target_company = company or "the company"
    target_role = title or "this role"

    why_change = (
        "I am looking for a role where I can take broader ownership "
        "of production data systems, solve larger-scale engineering "
        "problems, and continue growing across cloud, data platforms, "
        "automation, and AI-enabled workflows."
    )

    why_company = (
        f"I am interested in {target_company} because the "
        f"{target_role} opportunity aligns well with my background "
        "in production data engineering, automation, and reliable "
        "data platforms. I would like to contribute that experience "
        "while learning from a strong engineering environment."
    )

    answers = {
        "full_name": ApplicationAnswer(
            key="full_name",
            value=full_name,
            source="profile.identity",
            sensitive=True,
        ),
        "first_name": ApplicationAnswer(
            key="first_name",
            value=first_name,
            source="profile.identity",
            sensitive=True,
        ),
        "last_name": ApplicationAnswer(
            key="last_name",
            value=last_name,
            source="profile.identity",
            sensitive=True,
        ),
        "email": ApplicationAnswer(
            key="email",
            value=_text(
                getattr(
                    identity,
                    "email",
                    None,
                )
            ),
            source="profile.identity",
            sensitive=True,
        ),
        "phone": ApplicationAnswer(
            key="phone",
            value=_text(
                getattr(
                    identity,
                    "phone",
                    None,
                )
            ),
            source="profile.identity",
            sensitive=True,
        ),
        "current_location": ApplicationAnswer(
            key="current_location",
            value=_text(
                getattr(
                    identity,
                    "location",
                    None,
                )
            ),
            source="profile.identity",
        ),
        "linkedin_url": ApplicationAnswer(
            key="linkedin_url",
            value=_text(
                getattr(
                    identity,
                    "linkedin_url",
                    None,
                )
            ),
            source="profile.identity",
        ),
        "github_url": ApplicationAnswer(
            key="github_url",
            value=_text(
                getattr(
                    identity,
                    "github_url",
                    None,
                )
            ),
            source="profile.identity",
        ),
        "portfolio_url": ApplicationAnswer(
            key="portfolio_url",
            value=_text(
                getattr(
                    identity,
                    "portfolio_url",
                    None,
                )
            ),
            source="profile.identity",
        ),
        "current_company": ApplicationAnswer(
            key="current_company",
            value=company_name,
            source="profile.experience",
        ),
        "current_title": ApplicationAnswer(
            key="current_title",
            value=role_name,
            source="profile.experience",
        ),
        "total_experience_years": ApplicationAnswer(
            key="total_experience_years",
            value=getattr(
                profile,
                "total_experience_years",
                None,
            ),
            source="profile",
        ),
        "notice_period_days": ApplicationAnswer(
            key="notice_period_days",
            value=getattr(
                preferences,
                "notice_period_days",
                None,
            ),
            source="profile.preferences",
            review_required=True,
        ),
        "expected_compensation": ApplicationAnswer(
            key="expected_compensation",
            value=getattr(
                preferences,
                "expected_compensation",
                None,
            ),
            source="profile.preferences",
            sensitive=True,
            review_required=True,
        ),
        "why_change": ApplicationAnswer(
            key="why_change",
            value=why_change,
            source="deterministic_template",
            review_required=True,
        ),
        "why_company": ApplicationAnswer(
            key="why_company",
            value=why_company,
            source="deterministic_template",
            review_required=True,
        ),
    }

    return answers


def serialize_answer_bank(
    answers: dict[
        str,
        ApplicationAnswer,
    ],
) -> dict[str, dict]:
    return {key: answer.to_dict() for key, answer in answers.items()}
