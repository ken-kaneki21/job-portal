from __future__ import annotations

from dataclasses import asdict, dataclass

from jobintel.profile.universal import UniversalCandidateProfile


@dataclass(frozen=True)
class ApplicationAnswers:
    full_name: str | None
    first_name: str | None
    last_name: str | None
    email: str | None
    phone: str | None
    current_location: str | None
    linkedin_url: str | None
    github_url: str | None
    portfolio_url: str | None
    current_company: str | None
    current_title: str | None
    total_experience_years: float | None
    notice_period_days: int | None
    expected_compensation: str | None

    def to_dict(self) -> dict:
        return asdict(self)


def split_name(full_name: str | None) -> tuple[str | None, str | None]:
    if not full_name:
        return None, None
    parts = [value for value in full_name.strip().split() if value]
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], " ".join(parts[1:])


def current_experience(
    profile: UniversalCandidateProfile,
) -> tuple[str | None, str | None]:
    if not profile.experience:
        return None, None

    current = next(
        (
            entry
            for entry in profile.experience
            if entry.end_date and entry.end_date.strip().lower() == "present"
        ),
        profile.experience[0],
    )
    return current.company, current.title


def build_application_answers(
    profile: UniversalCandidateProfile,
) -> ApplicationAnswers:
    first_name, last_name = split_name(profile.identity.full_name)
    company, title = current_experience(profile)

    return ApplicationAnswers(
        full_name=profile.identity.full_name,
        first_name=first_name,
        last_name=last_name,
        email=profile.identity.email,
        phone=profile.identity.phone,
        current_location=profile.identity.location,
        linkedin_url=profile.identity.linkedin_url,
        github_url=profile.identity.github_url,
        portfolio_url=profile.identity.portfolio_url,
        current_company=company,
        current_title=title,
        total_experience_years=profile.total_experience_years,
        notice_period_days=profile.preferences.notice_period_days,
        expected_compensation=profile.preferences.expected_compensation,
    )
