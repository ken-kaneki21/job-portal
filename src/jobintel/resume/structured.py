from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from jobintel.profile.universal import (
    CandidateIdentity,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
)
from jobintel.resume.skills import (
    extract_skills,
)

SECTION_ALIASES: dict[
    str,
    set[str],
] = {
    "summary": {
        "summary",
        "profile summary",
        "professional summary",
        "profile",
        "professional profile",
        "about",
        "objective",
    },
    "skills": {
        "skills",
        "technical skills",
        "core skills",
        "technologies",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "employment history",
        "work history",
    },
    "projects": {
        "projects",
        "project experience",
        "personal projects",
        "academic projects",
        "key projects",
    },
    "education": {
        "education",
        "education & achievements",
        "education and achievements",
        "academic background",
        "academics",
        "qualifications",
    },
    "certifications": {
        "certifications",
        "certificates",
        "licenses & certifications",
        "licenses and certifications",
    },
}

EMAIL_RE = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)

PHONE_RE = re.compile(
    r"(?<!\d)" r"(?:\+?91[\s.-]?)?" r"(?:\d[\s.-]?){10}" r"(?!\d)",
)

URL_RE = re.compile(
    r"https?://[^\s|,;]+",
    re.IGNORECASE,
)

LINKEDIN_RE = re.compile(
    r"https?://(?:www\.)?" r"linkedin\.com/[^\s|,;]+",
    re.IGNORECASE,
)

GITHUB_RE = re.compile(
    r"https?://(?:www\.)?" r"github\.com/[^\s|,;]+",
    re.IGNORECASE,
)

MONTH_PATTERN = (
    r"(?:"
    r"Jan(?:uary)?|"
    r"Feb(?:ruary)?|"
    r"Mar(?:ch)?|"
    r"Apr(?:il)?|"
    r"May|"
    r"Jun(?:e)?|"
    r"Jul(?:y)?|"
    r"Aug(?:ust)?|"
    r"Sep(?:t(?:ember)?)?|"
    r"Oct(?:ober)?|"
    r"Nov(?:ember)?|"
    r"Dec(?:ember)?"
    r")"
)

DATE_TOKEN = rf"(?:{MONTH_PATTERN}\.?\s+\d{{4}}|\d{{4}})"

DATE_RANGE_RE = re.compile(
    rf"(?P<start>{DATE_TOKEN})"
    r"\s*(?:-|–|—|to)\s*"
    rf"(?P<end>{DATE_TOKEN}|Present|Current|Now)",
    re.IGNORECASE,
)

YEAR_RE = re.compile(
    r"\b(?:19|20)\d{2}\b",
)

EDUCATION_RE = re.compile(
    r"^(?P<degree>[^,]+),\s*"
    r"(?P<field>.+?)\s*"
    r"(?:—|–|-)\s*"
    r"(?P<institution>.+?)"
    r"(?:\s*\|\s*(?P<date>.+))?$",
)

MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

KNOWN_LOCATION_TERMS = (
    "bengaluru",
    "bangalore",
    "hyderabad",
    "pune",
    "mumbai",
    "delhi",
    "new delhi",
    "gurgaon",
    "gurugram",
    "noida",
    "chennai",
    "kolkata",
    "india",
)


@dataclass(
    frozen=True,
)
class ResumeStructure:
    identity: CandidateIdentity
    headline: str | None
    summary: str | None
    total_experience_years: float | None
    experience: list[ExperienceEntry]
    education: list[EducationEntry]
    projects: list[ProjectEntry]
    certifications: list[str]


def clean_line(
    value: str,
) -> str:
    return " ".join(value.strip().split())


def strip_bullet(
    value: str,
) -> str:
    cleaned = clean_line(
        value,
    )

    return re.sub(
        r"^[•●▪◦]\s*",
        "",
        cleaned,
    )


def is_bullet(
    value: str,
) -> bool:
    return clean_line(
        value,
    ).startswith(
        (
            "•",
            "●",
            "▪",
            "◦",
        )
    )


def normalized_heading(
    value: str,
) -> str:
    return (
        clean_line(
            value,
        )
        .lower()
        .rstrip(":")
    )


def heading_to_section(
    line: str,
) -> str | None:
    heading = normalized_heading(
        line,
    )

    for (
        section,
        aliases,
    ) in SECTION_ALIASES.items():
        if heading in aliases:
            return section

    return None


def split_resume_sections(
    resume_text: str,
) -> dict[
    str,
    list[str],
]:
    sections: dict[
        str,
        list[str],
    ] = {
        "header": [],
    }

    active_section = "header"

    for raw_line in resume_text.splitlines():
        cleaned = clean_line(
            raw_line,
        )

        if not cleaned:
            continue

        section = heading_to_section(
            cleaned,
        )

        if section is not None:
            active_section = section

            sections.setdefault(
                section,
                [],
            )

            continue

        sections.setdefault(
            active_section,
            [],
        ).append(
            cleaned,
        )

    return sections


def first_match(
    pattern: re.Pattern[str],
    text: str,
) -> str | None:
    match = pattern.search(
        text,
    )

    if match is None:
        return None

    return (
        match.group(
            0,
        )
        .strip()
        .rstrip(
            ".,;)",
        )
    )


def extract_name(
    header_lines: list[str],
) -> str | None:
    for line in header_lines[:5]:
        if EMAIL_RE.search(
            line,
        ):
            continue

        if PHONE_RE.search(
            line,
        ):
            continue

        lowered = line.lower()

        if "linkedin" in lowered:
            continue

        if "github" in lowered:
            continue

        if "|" in line:
            continue

        words = line.split()

        if not 1 <= len(words) <= 5:
            continue

        if not all(any(char.isalpha() for char in word) for word in words):
            continue

        return line

    return None


def extract_location(
    header_lines: list[str],
) -> str | None:
    for line in header_lines[:8]:
        parts = [
            clean_line(
                part,
            )
            for part in line.split("|")
        ]

        for part in parts:
            lowered = part.lower()

            if any(term == lowered or term in lowered for term in KNOWN_LOCATION_TERMS):
                return part

    return None


def extract_identity(
    resume_text: str,
    sections: dict[
        str,
        list[str],
    ],
) -> CandidateIdentity:
    header_lines = sections.get(
        "header",
        [],
    )

    linkedin = first_match(
        LINKEDIN_RE,
        resume_text,
    )

    github = first_match(
        GITHUB_RE,
        resume_text,
    )

    urls = [
        value.rstrip(
            ".,;)",
        )
        for value in URL_RE.findall(
            resume_text,
        )
    ]

    portfolio = next(
        (
            url
            for url in urls
            if url != linkedin
            and url != github
            and "linkedin.com" not in url.lower()
            and "github.com" not in url.lower()
        ),
        None,
    )

    return CandidateIdentity(
        full_name=extract_name(
            header_lines,
        ),
        email=first_match(
            EMAIL_RE,
            resume_text,
        ),
        phone=first_match(
            PHONE_RE,
            "\n".join(header_lines[:8]),
        ),
        location=extract_location(
            header_lines,
        ),
        linkedin_url=linkedin,
        github_url=github,
        portfolio_url=portfolio,
    )


def extract_summary(
    sections: dict[
        str,
        list[str],
    ],
) -> str | None:
    lines = sections.get(
        "summary",
        [],
    )

    if not lines:
        return None

    value = " ".join(
        lines,
    ).strip()

    return value or None


def headline_from_summary(
    summary: str | None,
) -> str | None:
    if summary is None:
        return None

    match = re.match(
        r"^(?P<headline>"
        r"[A-Za-z][A-Za-z0-9 /&+.-]{1,60}?"
        r")\s+with\s+"
        r"(?:\d+(?:\.\d+)?\+?\s+)?"
        r"years?\s+of",
        summary,
        flags=re.IGNORECASE,
    )

    if match is None:
        return None

    return clean_line(
        match.group(
            "headline",
        )
    )


def extract_headline(
    sections: dict[
        str,
        list[str],
    ],
    identity: CandidateIdentity,
    summary: str | None,
) -> str | None:
    summary_headline = headline_from_summary(
        summary,
    )

    if summary_headline:
        return summary_headline

    for line in sections.get(
        "header",
        [],
    ):
        if identity.full_name and line == identity.full_name:
            continue

        if "|" in line:
            continue

        if EMAIL_RE.search(
            line,
        ):
            continue

        if PHONE_RE.search(
            line,
        ):
            continue

        if len(line.split()) <= 12:
            return line

    return None


def parse_date_value(
    value: str,
    *,
    end_date: bool,
) -> datetime | None:
    cleaned = (
        value.strip()
        .lower()
        .replace(
            ".",
            "",
        )
    )

    if cleaned in {
        "present",
        "current",
        "now",
    }:
        return datetime.now(
            UTC,
        )

    parts = cleaned.split()

    try:
        if len(parts) == 1:
            year = int(
                parts[0],
            )

            return datetime(
                year,
                (12 if end_date else 1),
                1,
                tzinfo=UTC,
            )

        month = MONTHS.get(
            parts[0],
        )

        if month is None:
            return None

        year = int(
            parts[-1],
        )

        return datetime(
            year,
            month,
            1,
            tzinfo=UTC,
        )

    except ValueError:
        return None


def total_experience_from_ranges(
    ranges: list[tuple[str, str]],
) -> float | None:
    intervals: list[
        tuple[
            datetime,
            datetime,
        ]
    ] = []

    for (
        start_text,
        end_text,
    ) in ranges:
        start = parse_date_value(
            start_text,
            end_date=False,
        )

        end = parse_date_value(
            end_text,
            end_date=True,
        )

        if start is None or end is None or end < start:
            continue

        intervals.append(
            (
                start,
                end,
            )
        )

    if not intervals:
        return None

    intervals.sort(
        key=lambda item: item[0],
    )

    merged: list[list[datetime]] = []

    for start, end in intervals:
        if not merged:
            merged.append(
                [
                    start,
                    end,
                ]
            )

            continue

        previous = merged[-1]

        if start <= previous[1]:
            if end > previous[1]:
                previous[1] = end

            continue

        merged.append(
            [
                start,
                end,
            ]
        )

    total_days = sum((end - start).days for start, end in merged)

    if total_days <= 0:
        return None

    return round(
        total_days / 365.25,
        1,
    )


def is_experience_header(
    line: str,
) -> bool:
    return (
        "|" in line
        and DATE_RANGE_RE.search(
            line,
        )
        is not None
    )


def split_experience_blocks(
    lines: list[str],
) -> list[list[str]]:
    blocks: list[list[str]] = []

    current: list[str] = []

    for line in lines:
        if is_experience_header(
            line,
        ):
            if current:
                blocks.append(
                    current,
                )

            current = [
                line,
            ]

            continue

        if current:
            current.append(
                line,
            )

    if current:
        blocks.append(
            current,
        )

    return blocks


def parse_experience_block(
    block: list[str],
) -> ExperienceEntry | None:
    if not block:
        return None

    header = block[0]

    date_match = DATE_RANGE_RE.search(
        header,
    )

    if date_match is None:
        return None

    identity_part = header[: date_match.start()].strip(" |-–—")

    identity_parts = [
        clean_line(
            value,
        )
        for value in identity_part.split(
            "|",
            maxsplit=1,
        )
    ]

    title = identity_parts[0] if identity_parts else None

    company = identity_parts[1] if len(identity_parts) > 1 else None

    description_lines = [
        strip_bullet(
            line,
        )
        for line in block[1:]
    ]

    description = " ".join(line for line in description_lines if line).strip()

    skill_text = " ".join(
        block,
    )

    (
        core_skills,
        secondary_skills,
    ) = extract_skills(
        skill_text,
    )

    skills = list(dict.fromkeys(core_skills + secondary_skills))

    return ExperienceEntry(
        company=company,
        title=title,
        start_date=date_match.group(
            "start",
        ),
        end_date=date_match.group(
            "end",
        ),
        description=(description or None),
        skills=skills,
    )


def extract_experience(
    sections: dict[
        str,
        list[str],
    ],
) -> tuple[
    list[ExperienceEntry],
    float | None,
]:
    entries: list[ExperienceEntry] = []

    ranges: list[tuple[str, str]] = []

    blocks = split_experience_blocks(
        sections.get(
            "experience",
            [],
        )
    )

    for block in blocks:
        entry = parse_experience_block(
            block,
        )

        if entry is None:
            continue

        entries.append(
            entry,
        )

        if entry.start_date and entry.end_date:
            ranges.append(
                (
                    entry.start_date,
                    entry.end_date,
                )
            )

    return (
        entries,
        total_experience_from_ranges(
            ranges,
        ),
    )


def parse_project_header(
    header: str,
) -> tuple[
    str,
    list[str],
]:
    cleaned = clean_line(
        header,
    )

    cleaned = re.sub(
        r"\s+\b(?:19|20)\d{2}\b\s*$",
        "",
        cleaned,
    ).strip()

    bracket_match = re.search(
        r"\[(?P<skills>.+?)\]",
        cleaned,
    )

    skills: list[str] = []

    if bracket_match is not None:
        skill_text = bracket_match.group(
            "skills",
        )

        (
            core_skills,
            secondary_skills,
        ) = extract_skills(
            skill_text,
        )

        skills = list(dict.fromkeys(core_skills + secondary_skills))

        name = cleaned[: bracket_match.start()].strip()

    else:
        name = cleaned

    return (
        name,
        skills,
    )


def extract_projects(
    sections: dict[
        str,
        list[str],
    ],
) -> list[ProjectEntry]:
    lines = sections.get(
        "projects",
        [],
    )

    projects: list[ProjectEntry] = []

    current_header: list[str] = []
    current_description: list[str] = []

    def flush() -> None:
        nonlocal current_header
        nonlocal current_description

        if not current_header:
            return

        header = " ".join(
            current_header,
        )

        (
            name,
            header_skills,
        ) = parse_project_header(
            header,
        )

        description = " ".join(
            strip_bullet(
                line,
            )
            for line in current_description
        ).strip()

        (
            description_core,
            description_secondary,
        ) = extract_skills(
            " ".join(
                [
                    header,
                    description,
                ]
            )
        )

        skills = list(
            dict.fromkeys(header_skills + description_core + description_secondary)
        )

        if name:
            projects.append(
                ProjectEntry(
                    name=name,
                    description=(description or None),
                    skills=skills,
                )
            )

        current_header = []
        current_description = []

    for line in lines:
        new_project = (
            not is_bullet(
                line,
            )
            and "[" in line
        )

        if new_project:
            flush()

            current_header = [
                line,
            ]

            continue

        if not current_header:
            continue

        if not current_description and not is_bullet(
            line,
        ):
            current_header.append(
                line,
            )
            continue

        current_description.append(
            line,
        )

    flush()

    return projects


def extract_education(
    sections: dict[
        str,
        list[str],
    ],
) -> list[EducationEntry]:
    lines = sections.get(
        "education",
        [],
    )

    if not lines:
        return []

    first_line = lines[0]

    match = EDUCATION_RE.match(
        first_line,
    )

    if match is None:
        return []

    date_text = (
        match.group(
            "date",
        )
        or ""
    )

    years = [
        int(
            year,
        )
        for year in YEAR_RE.findall(
            date_text,
        )
    ]

    end_year = years[-1] if years else None

    return [
        EducationEntry(
            institution=clean_line(
                match.group(
                    "institution",
                )
            ),
            degree=clean_line(
                match.group(
                    "degree",
                )
            ),
            field=clean_line(
                match.group(
                    "field",
                )
            ),
            start_year=None,
            end_year=end_year,
        )
    ]


def extract_certifications(
    sections: dict[
        str,
        list[str],
    ],
) -> list[str]:
    lines = sections.get(
        "certifications",
        [],
    )

    if not lines:
        return []

    combined = " ".join(
        lines,
    )

    values = [
        clean_line(
            value,
        )
        for value in combined.split("|")
    ]

    return list(dict.fromkeys(value for value in values if value))


def extract_resume_structure(
    resume_text: str,
) -> ResumeStructure:
    sections = split_resume_sections(
        resume_text,
    )

    identity = extract_identity(
        resume_text,
        sections,
    )

    summary = extract_summary(
        sections,
    )

    (
        experience,
        total_experience_years,
    ) = extract_experience(
        sections,
    )

    return ResumeStructure(
        identity=identity,
        headline=extract_headline(
            sections,
            identity,
            summary,
        ),
        summary=summary,
        total_experience_years=(total_experience_years),
        experience=experience,
        education=extract_education(
            sections,
        ),
        projects=extract_projects(
            sections,
        ),
        certifications=(
            extract_certifications(
                sections,
            )
        ),
    )
