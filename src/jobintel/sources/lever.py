import hashlib
import re

import httpx

from jobintel.models.company import Company
from jobintel.models.fetched_job import FetchedJob
from jobintel.models.job import Job
from jobintel.sources.base import JobSource


BASE_URL = "https://api.lever.co/v0/postings"


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


class LeverSource(JobSource):

    def __init__(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        self.client = client

    async def fetch_jobs(
        self,
        company: Company,
    ) -> list[FetchedJob]:
        url = f"{BASE_URL}/{company.identifier}"

        response = await self.client.get(
            url,
            params={"mode": "json"},
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
            for raw in payload
        ]

    @staticmethod
    def _normalize(
        raw: dict,
        company: Company,
    ) -> Job:
        categories = raw.get("categories") or {}

        location = categories.get("location")
        department = categories.get("department")

        description = clean_text(
            raw.get("descriptionPlain")
            or raw.get("description")
        )

        title = raw["text"]

        fingerprint = make_fingerprint(
            company=company.name,
            title=title,
            location=location,
            description=description,
        )

        return Job(
            source="lever",
            source_identifier=company.identifier,
            external_id=str(raw["id"]),
            company=company.name,
            title=title,
            location=location,
            description=description,
            department=department,
            apply_url=raw["hostedUrl"],
            posted_at=None,
            updated_at=None,
            fingerprint=fingerprint,
        )