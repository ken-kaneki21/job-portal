import hashlib
import re

import httpx
from pydantic import HttpUrl

from jobintel.models.company import Company
from jobintel.models.fetched_job import FetchedJob
from jobintel.models.job import Job
from jobintel.sources.base import JobSource

BASE_URL = "https://api.smartrecruiters.com/v1/companies"

PAGE_SIZE = 100


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

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class SmartRecruitersSource(JobSource):
    def __init__(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        self.client = client

    async def fetch_jobs(
        self,
        company: Company,
    ) -> list[FetchedJob]:
        postings = []
        offset = 0

        while True:
            url = f"{BASE_URL}/{company.identifier}/postings"

            response = await self.client.get(
                url,
                params={
                    "limit": PAGE_SIZE,
                    "offset": offset,
                },
            )

            response.raise_for_status()

            payload = response.json()

            batch = payload.get("content", [])

            postings.extend(batch)

            total_found = payload.get(
                "totalFound",
                len(postings),
            )

            if not batch or len(postings) >= total_found:
                break

            offset += PAGE_SIZE

        fetched_jobs = []

        for raw in postings:
            detail = await self._fetch_detail(
                company=company,
                posting_id=str(raw["id"]),
            )

            fetched_jobs.append(
                FetchedJob(
                    job=self._normalize(
                        raw=detail,
                        company=company,
                    ),
                    raw=detail,
                )
            )

        return fetched_jobs

    async def _fetch_detail(
        self,
        company: Company,
        posting_id: str,
    ) -> dict:
        url = f"{BASE_URL}/{company.identifier}/postings/{posting_id}"

        response = await self.client.get(url)

        response.raise_for_status()

        return response.json()

    @staticmethod
    def _normalize(
        raw: dict,
        company: Company,
    ) -> Job:
        title = raw["name"]

        location_data = raw.get("location") or {}

        location_parts = [
            location_data.get("city"),
            location_data.get("region"),
            location_data.get("country"),
        ]

        location = ", ".join(part for part in location_parts if part) or None

        job_ad = raw.get("jobAd") or {}

        sections = job_ad.get("sections") or {}

        description_parts = []

        for value in sections.values():
            if isinstance(value, dict):
                text_value = value.get("text")

                if text_value:
                    description_parts.append(text_value)

        description = clean_text(" ".join(description_parts))

        department = (raw.get("department") or {}).get("label")

        external_id = str(raw["id"])

        apply_url = HttpUrl(str(raw.get("applyUrl") or raw.get("ref")))

        fingerprint = make_fingerprint(
            company=company.name,
            title=title,
            location=location,
            description=description,
        )

        return Job(
            source="smartrecruiters",
            source_identifier=company.identifier,
            external_id=external_id,
            company=company.name,
            title=title,
            location=location,
            description=description,
            department=department,
            apply_url=apply_url,
            posted_at=raw.get("releasedDate"),
            updated_at=None,
            fingerprint=fingerprint,
        )
