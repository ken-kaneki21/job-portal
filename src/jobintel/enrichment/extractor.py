import re
from dataclasses import asdict, dataclass

EXTRACTOR_VERSION = "deterministic_v2"


SKILL_PATTERNS: dict[
    str,
    tuple[str, ...],
] = {
    "python": ("python",),
    "sql": ("sql",),
    "pyspark": (
        "pyspark",
        "py spark",
    ),
    "spark": (
        "apache spark",
        "spark",
    ),
    "snowflake": ("snowflake",),
    "databricks": ("databricks",),
    "dbt": (
        "dbt",
        "data build tool",
    ),
    "airflow": (
        "airflow",
        "apache airflow",
    ),
    "azure data factory": (
        "azure data factory",
        "adf",
    ),
    "kafka": (
        "kafka",
        "apache kafka",
    ),
    "docker": ("docker",),
    "kubernetes": (
        "kubernetes",
        "k8s",
    ),
    "git": (
        "git",
        "github",
        "gitlab",
    ),
    "postgresql": (
        "postgresql",
        "postgres",
    ),
    "mysql": ("mysql",),
    "oracle": ("oracle",),
    "power bi": (
        "power bi",
        "powerbi",
    ),
    "tableau": ("tableau",),
    "terraform": ("terraform",),
    "fastapi": ("fastapi",),
    "redis": ("redis",),
    "temporal": ("temporal",),
    "mlflow": ("mlflow",),
    "pandas": ("pandas",),
    "etl": ("etl",),
    "elt": ("elt",),
    "data modeling": (
        "data modeling",
        "data modelling",
    ),
}


CLOUD_PATTERNS: dict[
    str,
    tuple[str, ...],
] = {
    "aws": (
        "aws",
        "amazon web services",
    ),
    "azure": (
        "azure",
        "microsoft azure",
    ),
    "gcp": (
        "gcp",
        "google cloud",
        "google cloud platform",
    ),
}


DATA_PLATFORM_PATTERNS: dict[
    str,
    tuple[str, ...],
] = {
    "snowflake": ("snowflake",),
    "databricks": ("databricks",),
    "bigquery": (
        "bigquery",
        "big query",
    ),
    "redshift": ("redshift",),
    "synapse": (
        "azure synapse",
        "synapse analytics",
    ),
    "fabric": ("microsoft fabric",),
}


REQUIRED_MARKERS = (
    "required",
    "must have",
    "must-have",
    "mandatory",
    "minimum qualification",
    "minimum qualifications",
    "requirements",
)


PREFERRED_MARKERS = (
    "preferred",
    "nice to have",
    "nice-to-have",
    "good to have",
    "plus",
    "bonus",
    "preferred qualification",
    "preferred qualifications",
)


RESPONSIBILITY_MARKERS = (
    "responsibilities",
    "key responsibilities",
    "role responsibilities",
    "what you'll do",
    "what you’ll do",
    "what you will do",
    "what you will be doing",
)


@dataclass(frozen=True)
class JobEnrichment:
    minimum_experience_years: int | None
    maximum_experience_years: int | None

    seniority: str | None
    employment_type: str | None
    education: str | None

    required_skills: list[str]
    preferred_skills: list[str]

    cloud_platforms: list[str]
    data_platforms: list[str]

    responsibilities: list[str]

    deal_breakers: list[str]

    def to_dict(
        self,
    ) -> dict:
        return asdict(self)


def normalize_text(
    value: str | None,
) -> str:
    if not value:
        return ""

    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip()


def lowercase(
    value: str | None,
) -> str:
    return normalize_text(value).lower()


def phrase_pattern(
    phrase: str,
) -> str:
    return r"(?<![a-z0-9])" + re.escape(phrase.lower()) + r"(?![a-z0-9])"


def phrase_exists(
    text: str,
    phrase: str,
) -> bool:
    return bool(
        re.search(
            phrase_pattern(phrase),
            text.lower(),
        )
    )


def extract_skill_names(
    text: str,
    patterns: dict[
        str,
        tuple[str, ...],
    ],
) -> list[str]:
    """
    Extract canonical skill names while avoiding
    overlapping aliases.

    Example:
        "Py Spark"

    should produce:
        pyspark

    and NOT:
        pyspark + spark
    """

    lowered = text.lower()

    candidates: list[
        tuple[
            int,
            int,
            int,
            str,
        ]
    ] = []

    for (
        canonical,
        aliases,
    ) in patterns.items():
        for alias in aliases:
            pattern = phrase_pattern(alias)

            for match in re.finditer(
                pattern,
                lowered,
            ):
                start = match.start()
                end = match.end()

                candidates.append(
                    (
                        -(end - start),
                        start,
                        end,
                        canonical,
                    )
                )

    candidates.sort()

    occupied: list[tuple[int, int]] = []

    found: set[str] = set()

    for (
        _negative_length,
        start,
        end,
        canonical,
    ) in candidates:
        overlaps = any(
            start < occupied_end and end > occupied_start
            for (
                occupied_start,
                occupied_end,
            ) in occupied
        )

        if overlaps:
            continue

        occupied.append(
            (
                start,
                end,
            )
        )

        found.add(canonical)

    return sorted(found)


def extract_experience_range(
    text: str,
) -> tuple[
    int | None,
    int | None,
]:
    normalized = lowercase(text)

    range_patterns = [
        (r"(\d+)\s*(?:-|–|to)\s*" r"(\d+)\s*(?:years|yrs)"),
    ]

    for pattern in range_patterns:
        match = re.search(
            pattern,
            normalized,
        )

        if match:
            return (
                int(match.group(1)),
                int(match.group(2)),
            )

    minimum_patterns = [
        (r"minimum\s+(?:of\s+)?" r"(\d+)\s*(?:years|yrs)"),
        (r"at\s+least\s+" r"(\d+)\s*(?:years|yrs)"),
        (r"(\d+)\+\s*" r"(?:years|yrs)"),
        (r"(\d+)\s*(?:years|yrs)" r"\s+of\s+experience"),
    ]

    values: list[int] = []

    for pattern in minimum_patterns:
        values.extend(
            int(value)
            for value in re.findall(
                pattern,
                normalized,
            )
        )

    if not values:
        return (
            None,
            None,
        )

    return (
        min(values),
        None,
    )


def extract_seniority(
    title: str,
    description: str,
) -> str | None:
    title_text = lowercase(title)

    combined = lowercase(f"{title} {description}")

    if any(
        value in title_text
        for value in (
            "principal",
            "staff",
        )
    ):
        return "staff_principal"

    if any(
        value in title_text
        for value in (
            "lead",
            "manager",
            "architect",
        )
    ):
        return "lead_manager"

    if "senior" in title_text:
        return "senior"

    if any(
        value in combined
        for value in (
            "entry level",
            "entry-level",
            "graduate",
            "fresher",
        )
    ):
        return "entry"

    if any(
        value in title_text
        for value in (
            "intern",
            "internship",
        )
    ):
        return "intern"

    return "mid"


def extract_employment_type(
    text: str,
) -> str | None:
    normalized = lowercase(text)

    patterns = [
        (
            "full_time",
            (
                "full time",
                "full-time",
                "permanent",
            ),
        ),
        (
            "contract",
            (
                "contract",
                "contractual",
            ),
        ),
        (
            "internship",
            (
                "internship",
                "intern",
            ),
        ),
        (
            "part_time",
            (
                "part time",
                "part-time",
            ),
        ),
    ]

    for (
        employment_type,
        aliases,
    ) in patterns:
        if any(alias in normalized for alias in aliases):
            return employment_type

    return None


def extract_education(
    text: str,
) -> str | None:
    normalized = lowercase(text)

    if any(
        value in normalized
        for value in (
            "master's degree",
            "masters degree",
            "m.tech",
            "mtech",
            "master degree",
        )
    ):
        return "masters"

    if any(
        value in normalized
        for value in (
            "bachelor's degree",
            "bachelors degree",
            "b.tech",
            "btech",
            "b.e.",
            "bachelor degree",
        )
    ):
        return "bachelors"

    if any(
        value in normalized
        for value in (
            "degree in computer science",
            "degree in engineering",
            "computer science degree",
        )
    ):
        return "degree"

    return None


def split_candidate_lines(
    description: str,
) -> list[str]:
    if not description:
        return []

    lines = re.split(
        r"[\n\r•]+",
        description,
    )

    cleaned: list[str] = []

    for line in lines:
        value = re.sub(
            r"\s+",
            " ",
            line,
        ).strip(" -\t")

        if not value:
            continue

        cleaned.append(value)

    return cleaned


def detect_section(
    line: str,
) -> str | None:
    normalized = lowercase(line).strip(" :.-")

    for marker in PREFERRED_MARKERS:
        if normalized.startswith(marker):
            return "preferred"

    for marker in RESPONSIBILITY_MARKERS:
        if normalized.startswith(marker):
            return "responsibilities"

    for marker in REQUIRED_MARKERS:
        if normalized.startswith(marker):
            return "required"

    return None


def is_section_heading(
    line: str,
) -> bool:
    """
    Identify heading-only lines such as:

        Requirements:
        Nice to have:
        Responsibilities:

    but not lines such as:

        Python is required.
    """

    normalized = lowercase(line).strip()

    stripped = normalized.strip(" :.-")

    known_headings = REQUIRED_MARKERS + PREFERRED_MARKERS + RESPONSIBILITY_MARKERS

    if stripped in known_headings:
        return True

    return False


def classify_skill_context(
    description: str,
) -> tuple[
    list[str],
    list[str],
]:
    lines = split_candidate_lines(description)

    required: set[str] = set()

    preferred: set[str] = set()

    unclassified: set[str] = set()

    current_section: str | None = None

    for line in lines:
        normalized = lowercase(line)

        detected_section = detect_section(line)

        if is_section_heading(line):
            current_section = detected_section

            continue

        line_skills = extract_skill_names(
            line,
            SKILL_PATTERNS,
        )

        if not line_skills:
            continue

        # -------------------------------------------------
        # Explicit inline preferred context wins.
        # -------------------------------------------------

        if any(marker in normalized for marker in PREFERRED_MARKERS):
            preferred.update(line_skills)

            if detected_section:
                current_section = detected_section

            continue

        # -------------------------------------------------
        # Explicit inline required context.
        # -------------------------------------------------

        if any(marker in normalized for marker in REQUIRED_MARKERS):
            required.update(line_skills)

            if detected_section:
                current_section = detected_section

            continue

        # -------------------------------------------------
        # Section-based classification.
        # -------------------------------------------------

        if current_section == "preferred":
            preferred.update(line_skills)

            continue

        if current_section == "required":
            required.update(line_skills)

            continue

        # -------------------------------------------------
        # Skills in Responsibilities are useful context,
        # but should NOT automatically become requirements.
        # -------------------------------------------------

        if current_section == "responsibilities":
            continue

        # -------------------------------------------------
        # Unsectioned skills default to required.
        #
        # This preserves previous behavior for simple JDs
        # that do not contain clear headings.
        # -------------------------------------------------

        unclassified.update(line_skills)

    required.update(unclassified)

    # If a skill appears in both places,
    # explicit required context wins.
    preferred -= required

    return (
        sorted(required),
        sorted(preferred),
    )


def extract_responsibilities(
    description: str,
) -> list[str]:
    lines = split_candidate_lines(description)

    verbs = (
        "build",
        "design",
        "develop",
        "maintain",
        "implement",
        "create",
        "optimize",
        "manage",
        "monitor",
        "collaborate",
        "architect",
        "support",
        "lead",
        "deliver",
        "own",
        "automate",
        "integrate",
    )

    responsibilities: list[str] = []

    for line in lines:
        normalized = lowercase(line)

        if any(
            re.search(
                rf"\b{verb}\w*\b",
                normalized,
            )
            for verb in verbs
        ):
            responsibilities.append(line[:500])

        if len(responsibilities) >= 10:
            break

    return responsibilities


def extract_deal_breakers(
    description: str,
) -> list[str]:
    normalized = lowercase(description)

    breakers: list[str] = []

    patterns = [
        (
            "security_clearance",
            (
                "security clearance",
                "active clearance",
            ),
        ),
        (
            "onsite_only",
            (
                "onsite only",
                "on-site only",
                "must work onsite",
            ),
        ),
        (
            "night_shift",
            (
                "night shift",
                "night shifts",
            ),
        ),
        (
            "travel_required",
            (
                "travel required",
                "willingness to travel",
                "must travel",
            ),
        ),
        (
            "visa_restriction",
            (
                "no visa sponsorship",
                "cannot sponsor visa",
                "must be authorized to work",
            ),
        ),
    ]

    for (
        name,
        aliases,
    ) in patterns:
        if any(alias in normalized for alias in aliases):
            breakers.append(name)

    return breakers


def extract_job_enrichment(
    *,
    title: str,
    description: str | None,
) -> JobEnrichment:
    description_text = description or ""

    combined = f"{title}\n{description_text}"

    (
        minimum_experience,
        maximum_experience,
    ) = extract_experience_range(combined)

    (
        required_skills,
        preferred_skills,
    ) = classify_skill_context(description_text)

    cloud_platforms = extract_skill_names(
        combined,
        CLOUD_PATTERNS,
    )

    data_platforms = extract_skill_names(
        combined,
        DATA_PLATFORM_PATTERNS,
    )

    return JobEnrichment(
        minimum_experience_years=(minimum_experience),
        maximum_experience_years=(maximum_experience),
        seniority=(
            extract_seniority(
                title,
                description_text,
            )
        ),
        employment_type=(extract_employment_type(combined)),
        education=(extract_education(combined)),
        required_skills=(required_skills),
        preferred_skills=(preferred_skills),
        cloud_platforms=(cloud_platforms),
        data_platforms=(data_platforms),
        responsibilities=(extract_responsibilities(description_text)),
        deal_breakers=(extract_deal_breakers(description_text)),
    )
