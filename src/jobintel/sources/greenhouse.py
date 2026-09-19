import hashlib
import html
import re

import httpx

from jobintel.models.company import Company
from jobintel.models.fetched_job import FetchedJob
from jobintel.models.job import Job
from jobintel.sources.base import JobSource

BASE_URL = "https://boards-api.greenhouse.io/v1/boards"


def clean_html(value: str | None) -> str | None:
    if not value:
        return None

    value = html.unescape(value)
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

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class GreenhouseSource(JobSource):
    def __init__(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        self.client = client

    async def fetch_jobs(
        self,
        company: Company,
    ) -> list[FetchedJob]:
        url = f"{BASE_URL}/{company.identifier}/jobs"

        response = await self.client.get(
            url,
            params={"content": "true"},
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
        departments = raw.get("departments") or []

        department = departments[0].get("name") if departments else None

        description = clean_html(raw.get("content"))

        location = (raw.get("location") or {}).get("name")

        fingerprint = make_fingerprint(
            company=company.name,
            title=raw["title"],
            location=location,
            description=description,
        )

        return Job(
            source="greenhouse",
            source_identifier=company.identifier,
            external_id=str(raw["id"]),
            company=company.name,
            title=raw["title"],
            location=location,
            description=description,
            department=department,
            apply_url=raw["absolute_url"],
            updated_at=raw.get("updated_at"),
            fingerprint=fingerprint,
        )
