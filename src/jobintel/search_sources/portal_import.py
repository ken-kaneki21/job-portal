from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import HttpUrl, ValidationError

from jobintel.models.fetched_job import FetchedJob
from jobintel.models.job import Job

SUPPORTED_PORTALS = {
    "linkedin",
    "naukri",
    "foundit",
    "indeed",
}

TITLE_FIELDS = (
    "title",
    "job_title",
    "job title",
    "position",
    "role",
)

COMPANY_FIELDS = (
    "company",
    "company_name",
    "company name",
    "employer",
    "organization",
)

LOCATION_FIELDS = (
    "location",
    "job_location",
    "job location",
    "city",
)

URL_FIELDS = (
    "apply_url",
    "apply url",
    "job_url",
    "job url",
    "url",
    "link",
)

ID_FIELDS = (
    "external_id",
    "external id",
    "job_id",
    "job id",
    "id",
)

DESCRIPTION_FIELDS = (
    "description",
    "job_description",
    "job description",
    "summary",
)

DEPARTMENT_FIELDS = (
    "department",
    "team",
    "function",
)

POSTED_FIELDS = (
    "posted_at",
    "posted at",
    "posted_date",
    "posted date",
    "date_posted",
    "date posted",
    "created_at",
)


class PortalImportError(ValueError):
    pass


@dataclass(frozen=True)
class PortalImportIssue:
    row_number: int
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PortalImportReport:
    portal: str
    path: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    jobs: tuple[FetchedJob, ...]
    issues: tuple[PortalImportIssue, ...]

    def summary_dict(self) -> dict:
        return {
            "portal": self.portal,
            "path": self.path,
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "invalid_rows": self.invalid_rows,
            "duplicate_rows": self.duplicate_rows,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def clean_text(
    value: Any,
) -> str | None:
    if value is None:
        return None

    cleaned = " ".join(str(value).strip().split())

    return cleaned or None


def normalize_key(
    value: Any,
) -> str:
    return (
        str(value)
        .strip()
        .lower()
        .replace(
            "-",
            "_",
        )
    )


def first_value(
    row: dict[str, Any],
    fields: tuple[str, ...],
) -> str | None:
    lowered = {normalize_key(key): value for key, value in row.items()}

    for field in fields:
        value = clean_text(lowered.get(normalize_key(field)))

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
    value = "|".join(
        [
            portal,
            url,
            company,
            title,
        ]
    )

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_posted_at(
    value: str | None,
) -> datetime | None:
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

    title = first_value(
        row,
        TITLE_FIELDS,
    )

    company = first_value(
        row,
        COMPANY_FIELDS,
    )

    url = first_value(
        row,
        URL_FIELDS,
    )

    if not title:
        raise PortalImportError("Job title is missing.")

    if not company:
        raise PortalImportError("Company is missing.")

    if not url:
        raise PortalImportError("Job/apply URL is missing.")

    location = first_value(
        row,
        LOCATION_FIELDS,
    )

    description = first_value(
        row,
        DESCRIPTION_FIELDS,
    )

    department = first_value(
        row,
        DEPARTMENT_FIELDS,
    )

    external_id = first_value(
        row,
        ID_FIELDS,
    )

    if not external_id:
        external_id = fallback_external_id(
            portal=(normalized_portal),
            url=url,
            company=company,
            title=title,
        )

    try:
        apply_url = HttpUrl(url)
    except ValidationError as exc:
        raise PortalImportError("Job/apply URL is invalid.") from exc

    job = Job(
        source=normalized_portal,
        source_identifier=(normalized_portal),
        external_id=external_id,
        company=company,
        title=title,
        location=location,
        description=description,
        department=department,
        apply_url=apply_url,
        posted_at=parse_posted_at(
            first_value(
                row,
                POSTED_FIELDS,
            )
        ),
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


def sniff_delimiter(
    sample: str,
) -> str:
    try:
        dialect = csv.Sniffer().sniff(
            sample,
            delimiters=",;\t|",
        )

        return dialect.delimiter

    except csv.Error:
        return ","


def read_csv_records(
    path: Path,
) -> list[dict[str, Any]]:
    text = path.read_text(
        encoding="utf-8-sig",
    )

    reader = csv.DictReader(
        text.splitlines(),
        delimiter=sniff_delimiter(text[:8192]),
    )

    return [dict(row) for row in reader]


def read_json_records(
    path: Path,
) -> list[dict[str, Any]]:
    payload: Any = json.loads(
        path.read_text(
            encoding="utf-8-sig",
        )
    )

    records: list[Any]

    if isinstance(
        payload,
        list,
    ):
        records = payload

    elif isinstance(
        payload,
        dict,
    ):
        candidate: Any = (
            payload.get("jobs")
            or payload.get("results")
            or payload.get("items")
            or payload.get("data")
        )

        if not isinstance(
            candidate,
            list,
        ):
            raise PortalImportError(
                "JSON must be a list or contain jobs/results/items/data."
            )

        records = candidate

    else:
        raise PortalImportError("Unsupported JSON structure.")

    return [
        record
        for record in records
        if isinstance(
            record,
            dict,
        )
    ]


def read_records(
    path: Path,
) -> list[dict[str, Any]]:
    if not path.exists():
        raise PortalImportError(f"Import file not found: {path}")

    suffix = path.suffix.lower()

    if suffix in {
        ".csv",
        ".tsv",
    }:
        return read_csv_records(path)

    if suffix == ".json":
        return read_json_records(path)

    raise PortalImportError("Only CSV, TSV, and JSON imports are supported.")


def imported_with_provenance(
    fetched: FetchedJob,
    *,
    path: Path,
    row_number: int,
) -> FetchedJob:
    return FetchedJob(
        job=fetched.job,
        raw={
            **fetched.raw,
            "import_provenance": {
                "filename": path.name,
                "row_number": (row_number),
                "imported_at": (datetime.now(UTC).isoformat()),
            },
        },
    )


def inspect_portal_file(
    *,
    portal: str,
    path: Path,
) -> PortalImportReport:
    normalized_portal = portal.strip().lower()

    if normalized_portal not in SUPPORTED_PORTALS:
        raise PortalImportError("Unsupported portal: " + portal)

    records = read_records(path)

    jobs: list[FetchedJob] = []

    issues: list[PortalImportIssue] = []

    seen: set[tuple[str, str]] = set()

    duplicates = 0

    for index, row in enumerate(
        records,
        start=1,
    ):
        try:
            fetched = normalize_portal_job(
                portal=(normalized_portal),
                row=row,
            )

        except (
            PortalImportError,
            ValueError,
        ) as exc:
            issues.append(
                PortalImportIssue(
                    row_number=index,
                    message=str(exc),
                )
            )

            continue

        identity = (
            fetched.job.source_identifier,
            fetched.job.external_id,
        )

        if identity in seen:
            duplicates += 1
            continue

        seen.add(identity)

        jobs.append(
            imported_with_provenance(
                fetched,
                path=path,
                row_number=index,
            )
        )

    if not jobs and issues:
        preview = " | ".join(
            (f"row {issue.row_number}: {issue.message}") for issue in issues[:5]
        )

        raise PortalImportError("No valid jobs were imported. " + preview)

    return PortalImportReport(
        portal=normalized_portal,
        path=str(path),
        total_rows=len(records),
        valid_rows=len(jobs),
        invalid_rows=len(issues),
        duplicate_rows=(duplicates),
        jobs=tuple(jobs),
        issues=tuple(issues),
    )


def load_portal_file(
    *,
    portal: str,
    path: Path,
) -> list[FetchedJob]:
    report = inspect_portal_file(
        portal=portal,
        path=path,
    )

    return list(report.jobs)
