from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import HttpUrl

from jobintel.models.fetched_job import FetchedJob
from jobintel.models.job import Job

SUPPORTED_PORTALS = {
    "linkedin",
    "naukri",
    "foundit",
    "indeed",
}

TITLE_FIELDS = ("title", "job_title", "position", "role")
COMPANY_FIELDS = ("company", "company_name", "employer", "organization")
LOCATION_FIELDS = ("location", "job_location", "city")
URL_FIELDS = ("apply_url", "job_url", "url", "link")
ID_FIELDS = ("external_id", "job_id", "id")
DESCRIPTION_FIELDS = ("description", "job_description", "summary")
DEPARTMENT_FIELDS = ("department", "team", "function")
POSTED_FIELDS = ("posted_at", "posted_date", "date_posted", "created_at")


class PortalImportError(ValueError):
    pass


def clean_text(value: Any) -> str | None:
    if value is None:
        return None

    cleaned = " ".join(str(value).strip().split())
    return cleaned or None


def first_value(
    row: dict[str, Any],
    fields: tuple[str, ...],
) -> str | None:
    lowered = {str(key).strip().lower(): value for key, value in row.items()}

    for field in fields:
        value = clean_text(lowered.get(field))
        if value:
            return value

    return None


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


def fallback_external_id(
    *,
    portal: str,
    url: str,
    company: str,
    title: str,
) -> str:
    value = "|".join([portal, url, company, title])
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_posted_at(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def normalize_portal_job(
    *,
    portal: str,
    row: dict[str, Any],
) -> FetchedJob:
    normalized_portal = portal.strip().lower()

    if normalized_portal not in SUPPORTED_PORTALS:
        raise PortalImportError("Unsupported portal: " + portal)

    title = first_value(row, TITLE_FIELDS)
    company = first_value(row, COMPANY_FIELDS)
    url = first_value(row, URL_FIELDS)

    if not title:
        raise PortalImportError("Job title is missing.")
    if not company:
        raise PortalImportError("Company is missing.")
    if not url:
        raise PortalImportError("Job/apply URL is missing.")

    location = first_value(row, LOCATION_FIELDS)
    description = first_value(row, DESCRIPTION_FIELDS)
    department = first_value(row, DEPARTMENT_FIELDS)
    external_id = first_value(row, ID_FIELDS)

    if not external_id:
        external_id = fallback_external_id(
            portal=normalized_portal,
            url=url,
            company=company,
            title=title,
        )

    posted_at = parse_posted_at(first_value(row, POSTED_FIELDS))

    job = Job(
        source=normalized_portal,
        source_identifier=normalized_portal,
        external_id=external_id,
        company=company,
        title=title,
        location=location,
        description=description,
        department=department,
        apply_url=HttpUrl(url),
        posted_at=posted_at,
        updated_at=None,
        fingerprint=make_fingerprint(
            company=company,
            title=title,
            location=location,
            description=description,
        ),
    )

    return FetchedJob(
        job=job,
        raw={
            "portal": normalized_portal,
            "imported": True,
            "payload": row,
        },
    )


def read_csv_records(path: Path) -> list[dict[str, Any]]:
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        candidate = (
            payload.get("jobs") or payload.get("results") or payload.get("items")
        )
        if not isinstance(candidate, list):
            raise PortalImportError(
                "JSON must be a list or contain jobs/results/items."
            )
        records = candidate
    else:
        raise PortalImportError("Unsupported JSON structure.")

    return [record for record in records if isinstance(record, dict)]


def load_portal_file(
    *,
    portal: str,
    path: Path,
) -> list[FetchedJob]:
    suffix = path.suffix.lower()

    if suffix == ".csv":
        records = read_csv_records(path)
    elif suffix == ".json":
        records = read_json_records(path)
    else:
        raise PortalImportError("Only CSV and JSON imports are supported.")

    jobs: list[FetchedJob] = []
    errors: list[str] = []

    for index, row in enumerate(records, start=1):
        try:
            jobs.append(
                normalize_portal_job(
                    portal=portal,
                    row=row,
                )
            )
        except (PortalImportError, ValueError) as exc:
            errors.append(f"row {index}: {exc}")

    if not jobs and errors:
        raise PortalImportError(
            "No valid jobs were imported. " + " | ".join(errors[:5])
        )

    return jobs
