import hashlib
import re

import httpx

from jobintel.models.company import Company
from jobintel.models.fetched_job import FetchedJob
from jobintel.models.job import Job
from jobintel.sources.base import JobSource


BASE_URL = "https://api.ashbyhq.com/posting-api/job-board"


def clean_text(value: str | None) -> str | None:
    if not value:
        return None

    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def make_fingerprint(
    company: str,
    title: str,
    location: str | None,
    description: str | None,
) -> str:
    content = "|".join(
        [
            company.strip().lower(),
            title.strip().lower(),
            (location or "").strip().lower(),
            (description or "").strip().lower(),
        ]
    )

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


class AshbySource(JobSource):

    def __init__(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        self.client = client

    async def fetch_jobs(
        self,
        company: Company,
    ) -> list[FetchedJob]:
        url = (
            f"{BASE_URL}/"
            f"{company.identifier}"
        )

        response = await self.client.get(
            url,
            params={
                "includeCompensation": "true"
            },
        )

        response.raise_for_status()

        payload = response.json()

        return [
            FetchedJob(
                job=self._normalize(
                    raw=raw,
                    company=company,
                ),
                raw=raw,
            )
            for raw in payload.get("jobs", [])
        ]

    @staticmethod
    def _normalize(
        raw: dict,
        company: Company,
    ) -> Job:
        title = raw["title"]

        location = raw.get("location")

        description = clean_text(
            raw.get("descriptionPlain")
            or raw.get("descriptionHtml")
        )

        department = (
            raw.get("department")
            or raw.get("team")
        )

        external_id = str(
            raw.get("id")
            or raw.get("jobUrl")
        )

        apply_url = (
            raw.get("applyUrl")
            or raw.get("jobUrl")
        )

        fingerprint = make_fingerprint(
            company=company.name,
            title=title,
            location=location,
            description=description,
        )

        return Job(
            source="ashby",
            source_identifier=company.identifier,
            external_id=external_id,
            company=company.name,
            title=title,
            location=location,
            description=description,
            department=department,
            apply_url=apply_url,
            posted_at=raw.get("publishedAt"),
            updated_at=None,
            fingerprint=fingerprint,
        )