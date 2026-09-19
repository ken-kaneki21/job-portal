import re
from dataclasses import dataclass

import httpx


@dataclass
class ATSResolution:
    ats: str
    identifier: str
    career_url: str


def normalize_slug(
    value: str,
) -> str:
    value = value.lower().strip()

    value = re.sub(
        r"[^a-z0-9]+",
        "",
        value,
    )

    return value


def build_slug_candidates(
    company_name: str,
) -> list[str]:
    """
    Generate realistic ATS identifiers from
    a broad-search company name.
    """

    original = (
        company_name
        .lower()
        .strip()
    )

    words = re.findall(
        r"[a-z0-9]+",
        original,
    )

    stop_words = {
        "inc",
        "incorporated",
        "llc",
        "ltd",
        "limited",
        "private",
        "pvt",
        "company",
        "corp",
        "corporation",
        "technologies",
        "technology",
        "solutions",
        "services",
        "india",
    }

    cleaned_words = [
        word
        for word in words
        if word not in stop_words
    ]

    candidates = []

    raw_slug = normalize_slug(
        company_name
    )

    if raw_slug:
        candidates.append(
            raw_slug
        )

    if cleaned_words:
        joined = "".join(
            cleaned_words
        )

        hyphenated = "-".join(
            cleaned_words
        )

        candidates.extend(
            [
                joined,
                hyphenated,
            ]
        )

    if words:
        candidates.append(
            "".join(words)
        )

        candidates.append(
            "-".join(words)
        )

    # preserve order while removing duplicates
    result = []

    seen = set()

    for candidate in candidates:
        candidate = candidate.strip()

        if not candidate:
            continue

        if candidate in seen:
            continue

        seen.add(
            candidate
        )

        result.append(
            candidate
        )

    return result[:6]


def response_has_jobs(
    response: httpx.Response,
) -> bool:
    if response.status_code != 200:
        return False

    try:
        data = response.json()
    except Exception:
        return False

    if isinstance(
        data,
        list,
    ):
        return len(data) > 0

    if not isinstance(
        data,
        dict,
    ):
        return False

    if isinstance(
        data.get("jobs"),
        list,
    ):
        return len(
            data["jobs"]
        ) > 0

    if isinstance(
        data.get("content"),
        list,
    ):
        return len(
            data["content"]
        ) > 0

    if isinstance(
        data.get("data"),
        list,
    ):
        return len(
            data["data"]
        ) > 0

    if (
        isinstance(
            data.get("totalFound"),
            int,
        )
        and data["totalFound"] > 0
    ):
        return True

    return False


def probe_greenhouse(
    client: httpx.Client,
    slug: str,
) -> ATSResolution | None:
    url = (
        "https://boards-api.greenhouse.io/"
        f"v1/boards/{slug}/jobs"
    )

    response = client.get(
        url
    )

    if not response_has_jobs(
        response
    ):
        return None

    return ATSResolution(
        ats="greenhouse",
        identifier=slug,
        career_url=(
            f"https://job-boards.greenhouse.io/{slug}"
        ),
    )


def probe_lever(
    client: httpx.Client,
    slug: str,
) -> ATSResolution | None:
    url = (
        "https://api.lever.co/v0/"
        f"postings/{slug}"
    )

    response = client.get(
        url,
        params={
            "mode": "json",
        },
    )

    if not response_has_jobs(
        response
    ):
        return None

    return ATSResolution(
        ats="lever",
        identifier=slug,
        career_url=(
            f"https://jobs.lever.co/{slug}"
        ),
    )


def probe_ashby(
    client: httpx.Client,
    slug: str,
) -> ATSResolution | None:
    url = (
        "https://api.ashbyhq.com/"
        f"posting-api/job-board/{slug}"
    )

    response = client.get(
        url
    )

    if not response_has_jobs(
        response
    ):
        return None

    return ATSResolution(
        ats="ashby",
        identifier=slug,
        career_url=(
            f"https://jobs.ashbyhq.com/{slug}"
        ),
    )


def probe_smartrecruiters(
    client: httpx.Client,
    slug: str,
) -> ATSResolution | None:
    url = (
        "https://api.smartrecruiters.com/"
        f"v1/companies/{slug}/postings"
    )

    response = client.get(
        url,
        params={
            "limit": 1,
        },
    )

    if not response_has_jobs(
        response
    ):
        return None

    return ATSResolution(
        ats="smartrecruiters",
        identifier=slug,
        career_url=(
            "https://careers."
            f"smartrecruiters.com/{slug}"
        ),
    )


def resolve_company_ats(
    company_name: str,
) -> ATSResolution | None:
    slugs = build_slug_candidates(
        company_name
    )

    with httpx.Client(
        timeout=8.0,
        follow_redirects=True,
        headers={
            "User-Agent": (
                "JobIntel/1.0 ATS discovery"
            )
        },
    ) as client:
        for slug in slugs:
            probes = [
                probe_greenhouse,
                probe_lever,
                probe_ashby,
                probe_smartrecruiters,
            ]

            for probe in probes:
                try:
                    result = probe(
                        client,
                        slug,
                    )

                except httpx.HTTPError:
                    continue

                if result is not None:
                    return result

    return None