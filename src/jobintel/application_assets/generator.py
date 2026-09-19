from dataclasses import asdict, dataclass
from typing import Any

GENERATOR_VERSION = "deterministic_assets_v1"


@dataclass(frozen=True)
class ApplicationAssets:
    recruiter_dm: str
    email_subject: str
    email_body: str
    cover_note: str
    resume_summary: str

    skills_to_emphasize: list[str]
    missing_skills_warning: list[str]

    resume_bullets_to_emphasize: list[str]
    interview_talking_points: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def clean_values(
    values: list[str] | None,
) -> list[str]:
    if not values:
        return []

    return sorted(
        {str(value).strip() for value in values if value and str(value).strip()}
    )


def profile_skills(
    profile: Any,
) -> set[str]:
    values: set[str] = set()

    for attribute in (
        "core_skills",
        "secondary_skills",
    ):
        skills = getattr(
            profile,
            attribute,
            None,
        )

        if not skills:
            continue

        values.update(str(skill).strip().lower() for skill in skills if skill)

    return values


def pretty_skills(
    values: list[str],
    limit: int = 6,
) -> str:
    selected = values[:limit]

    if not selected:
        return "relevant data engineering skills"

    return ", ".join(selected)


def build_skills_to_emphasize(
    *,
    profile: Any,
    gap,
) -> list[str]:
    candidate_skills = profile_skills(profile)

    matched = (
        clean_values(gap.matched_required_skills)
        + clean_values(gap.matched_preferred_skills)
        + clean_values(gap.matched_platforms)
    )

    result: list[str] = []

    for skill in matched:
        if skill.lower() in candidate_skills and skill not in result:
            result.append(skill)

    if result:
        return result[:10]

    fallback = []

    for attribute in (
        "core_skills",
        "secondary_skills",
    ):
        values = getattr(
            profile,
            attribute,
            None,
        )

        if not values:
            continue

        for value in values:
            cleaned = str(value).strip()

            if cleaned and cleaned not in fallback:
                fallback.append(cleaned)

    return fallback[:10]


def build_missing_skills(
    gap,
) -> list[str]:
    values = (
        clean_values(gap.missing_required_skills)
        + clean_values(gap.missing_preferred_skills)
        + clean_values(gap.missing_platforms)
    )

    result: list[str] = []

    for value in values:
        if value not in result:
            result.append(value)

    return result[:10]


def build_resume_bullets(
    *,
    skills: list[str],
    job_title: str,
) -> list[str]:
    focus = pretty_skills(
        skills,
        limit=5,
    )

    return [
        (
            "Highlight production data pipeline work "
            f"most relevant to {job_title}, especially "
            f"{focus}."
        ),
        (
            "Emphasize measurable ETL/ELT, data quality, "
            "reliability, performance, or automation outcomes."
        ),
        (
            "Prioritize examples showing ownership from "
            "source ingestion through transformation, "
            "validation, and production delivery."
        ),
        (
            "Mention cloud, orchestration, warehouse, and "
            "distributed processing technologies only where "
            "you have actually used them."
        ),
    ]


def build_interview_points(
    *,
    job_title: str,
    skills: list[str],
    gap,
) -> list[str]:
    result = [
        (
            f"Explain a production data-engineering project "
            f"that maps closely to the {job_title} role."
        ),
        (
            "Be ready to describe architecture choices, "
            "failure handling, validation, observability, "
            "and performance optimization."
        ),
    ]

    if skills:
        result.append("Prepare concrete examples using: " + ", ".join(skills[:6]) + ".")

    missing = clean_values(gap.missing_required_skills)

    if missing:
        result.append(
            "Prepare an honest bridge explanation for: " + ", ".join(missing[:5]) + "."
        )

    if gap.experience_fit == "below_requirement":
        result.append(
            "Address the experience gap by emphasizing "
            "scope, ownership, complexity, and measurable "
            "impact rather than inflating years of experience."
        )

    return result


def generate_application_assets(
    *,
    profile: Any,
    job,
    enrichment,
    gap,
    ranking,
) -> ApplicationAssets:
    skills = build_skills_to_emphasize(
        profile=profile,
        gap=gap,
    )

    missing = build_missing_skills(gap)

    skill_text = pretty_skills(skills)

    location = job.location or "the listed location"

    recruiter_dm = (
        f"Hi, I came across the {job.title} opening at "
        f"{job.company}. My background in {skill_text} "
        f"aligns well with the role. I’d be interested in "
        f"connecting and sharing my resume for consideration."
    )

    email_subject = f"Application interest – {job.title} | {job.company}"

    email_body = (
        f"Hi,\n\n"
        f"I’m reaching out regarding the {job.title} role at "
        f"{job.company} in {location}. My data engineering "
        f"experience includes {skill_text}, along with "
        f"building and maintaining production data pipelines.\n\n"
        f"The role appears closely aligned with my background, "
        f"and I would appreciate the opportunity to be considered. "
        f"I’m happy to share my resume and discuss the position "
        f"in more detail.\n\n"
        f"Regards"
    )

    cover_note = (
        f"I’m interested in the {job.title} position at "
        f"{job.company}. My background includes hands-on work "
        f"with {skill_text}, production ETL/ELT pipelines, "
        f"data quality, automation, and cloud data platforms. "
        f"The role aligns with my experience building reliable "
        f"data workflows and translating business requirements "
        f"into maintainable data solutions."
    )

    resume_summary = (
        f"Data Engineer with hands-on experience in "
        f"{skill_text}, ETL/ELT pipeline development, "
        f"data quality, cloud data platforms, automation, "
        f"and production-oriented engineering practices."
    )

    resume_bullets = build_resume_bullets(
        skills=skills,
        job_title=job.title,
    )

    talking_points = build_interview_points(
        job_title=job.title,
        skills=skills,
        gap=gap,
    )

    return ApplicationAssets(
        recruiter_dm=(recruiter_dm),
        email_subject=(email_subject),
        email_body=(email_body),
        cover_note=(cover_note),
        resume_summary=(resume_summary),
        skills_to_emphasize=(skills),
        missing_skills_warning=(missing),
        resume_bullets_to_emphasize=(resume_bullets),
        interview_talking_points=(talking_points),
    )
