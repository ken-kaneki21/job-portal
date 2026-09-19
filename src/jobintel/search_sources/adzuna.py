import hashlib
import os
import re

import httpx
from dotenv import load_dotenv

from jobintel.models.fetched_job import FetchedJob
from jobintel.models.job import Job
from jobintel.search_sources.base import SearchSource


load_dotenv()


BASE_URL = "https://api.adzuna.com/v1/api/jobs"

RESULTS_PER_PAGE = 50


def clean_text(
    value: str | None,
) -> str | None:
    if not value:
        return None

    value = re.sub(
        r"<[^>]+>",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

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


class AdzunaSource(SearchSource):

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        country: str = "in",
    ) -> None:
        self.client = client
        self.country = country

        self.app_id = os.getenv(
            "ADZUNA_APP_ID"
        )

        self.app_key = os.getenv(
            "ADZUNA_APP_KEY"
        )

        if not self.app_id:
            raise RuntimeError(
                "ADZUNA_APP_ID is missing."
            )

        if not self.app_key:
            raise RuntimeError(
                "ADZUNA_APP_KEY is missing."
            )

    async def search_jobs(
        self,
        *,
        query: str,
        location: str | None = None,
        max_pages: int = 1,
    ) -> list[FetchedJob]:
        results: list[FetchedJob] = []

        for page in range(
            1,
            max_pages + 1,
        ):
            url = (
                f"{BASE_URL}/"
                f"{self.country}/search/{page}"
            )

            params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "results_per_page":
                    RESULTS_PER_PAGE,
                "what": query,
                "content-type":
                    "application/json",
            }

            if location:
                params["where"] = location

            response = await self.client.get(
                url,
                params=params,
                headers={
                    "Accept":
                        "application/json"
                },
            )

            response.raise_for_status()

            payload = response.json()

            batch = payload.get(
                "results",
                [],
            )

            if not batch:
                break

            results.extend(
                self._normalize_batch(
                    batch
                )
            )

            if (
                len(batch)
                < RESULTS_PER_PAGE
            ):
                break

        return results

    def _normalize_batch(
        self,
        batch: list[dict],
    ) -> list[FetchedJob]:
        return [
            FetchedJob(
                job=self._normalize(raw),
                raw=raw,
            )
            for raw in batch
        ]

    def _normalize(
        self,
        raw: dict,
    ) -> Job:
        company_data = (
            raw.get("company")
            or {}
        )

        company = (
            company_data.get(
                "display_name"
            )
            or "Unknown"
        )

        location_data = (
            raw.get("location")
            or {}
        )

        location = (
            location_data.get(
                "display_name"
            )
        )

        title = (
            raw.get("title")
            or "Unknown"
        )

        description = clean_text(
            raw.get("description")
        )

        external_id = str(
            raw.get("id")
        )

        apply_url = (
            raw.get("redirect_url")
            or ""
        )

        fingerprint = make_fingerprint(
            company=company,
            title=title,
            location=location,
            description=description,
        )

        return Job(
            source="adzuna",
            source_identifier=(
                f"{self.country}"
            ),
            external_id=external_id,
            company=company,
            title=title,
            location=location,
            department=None,
            description=description,
            apply_url=apply_url,
            posted_at=raw.get(
                "created"
            ),
            updated_at=None,
            fingerprint=fingerprint,
        )