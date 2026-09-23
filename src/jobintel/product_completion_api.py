from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from jobintel.db.broad_repository import persist_broad_jobs
from jobintel.db.session import SessionLocal
from jobintel.search_sources.portal_import import (
    SUPPORTED_PORTALS,
    PortalImportError,
    load_portal_file,
)

router = APIRouter(tags=["product-completion"])

_ALLOWED_SUFFIXES = {".csv", ".json"}

_SKILLS = (
    "python",
    "sql",
    "pyspark",
    "spark",
    "snowflake",
    "databricks",
    "airflow",
    "dbt",
    "azure",
    "aws",
    "gcp",
    "kafka",
    "docker",
    "kubernetes",
    "power bi",
    "tableau",
    "fabric",
    "llm",
    "rag",
    "genai",
    "machine learning",
    "ml",
)

_ROLE_PATTERNS = (
    r"(?:hiring|looking for|opening for|role[:\s]+)\s+(?:an?\s+)?([A-Za-z0-9 /&+.-]{3,80})",
    r"(Data Engineer|Senior Data Engineer|Data Analyst|AI Engineer|ML Engineer|"
    r"Machine Learning Engineer|Analytics Engineer|Data Scientist|"
    r"GenAI Engineer|Software Engineer)",
)

_LOCATION_PATTERN = re.compile(
    r"\b(Bengaluru|Bangalore|Hyderabad|Pune|Mumbai|Delhi|Gurgaon|Gurugram|"
    r"Noida|Chennai|India|Remote|Hybrid)\b",
    re.IGNORECASE,
)

_EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class HiringPostRequest(BaseModel):
    text: str = Field(min_length=10, max_length=20000)
    source_url: str | None = Field(default=None, max_length=2000)


def _clean(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip(" -:|\t\r\n")
    return cleaned or None


def extract_hiring_post(text: str, source_url: str | None = None) -> dict:
    normalized = re.sub(r"\r\n?", "\n", text).strip()
    flat = re.sub(r"\s+", " ", normalized)

    role = None
    for pattern in _ROLE_PATTERNS:
        match = re.search(pattern, flat, re.IGNORECASE)
        if match:
            role = _clean(match.group(1))
            if role:
                role = re.split(
                    r"\b(?:at|for|in|with|location|experience|exp)\b",
                    role,
                    maxsplit=1,
                    flags=re.IGNORECASE,
                )[0].strip(" -:|")
            break

    company = None
    company_match = re.search(
        r"\b(?:at|company[:\s]+)\s+([A-Z][A-Za-z0-9&.,' -]{1,80})",
        flat,
    )
    if company_match:
        company = _clean(company_match.group(1))
        if company:
            company = re.split(
                r"\b(?:is hiring|hiring|for|location|based|we are)\b",
                company,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0].strip(" -:|")

    location_match = _LOCATION_PATTERN.search(flat)
    location = _clean(location_match.group(1)) if location_match else None

    emails = sorted(set(_EMAIL_PATTERN.findall(flat)))

    lowered = flat.lower()
    skills = sorted(
        {
            skill
            for skill in _SKILLS
            if re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", lowered)
        }
    )

    experience = None
    experience_match = re.search(
        r"\b(\d{1,2})\s*(?:\+|-\s*\d{1,2})?\s*(?:years?|yrs?)\b",
        flat,
        re.IGNORECASE,
    )
    if experience_match:
        experience = int(experience_match.group(1))

    return {
        "role": role,
        "company": company,
        "location": location,
        "skills": skills,
        "minimum_experience_years": experience,
        "contact_emails": emails,
        "source_url": source_url,
        "review_required": True,
        "auto_apply": False,
        "raw_text": normalized,
    }


@router.get("/integrations/portals")
def portal_integrations() -> dict:
    return {
        "supported_portals": sorted(SUPPORTED_PORTALS),
        "accepted_file_types": sorted(_ALLOWED_SUFFIXES),
        "review_required": True,
        "credential_scraping": False,
    }


@router.post("/integrations/portal-import")
async def import_portal_jobs(
    portal: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
    session: Session = Depends(get_db),
) -> dict:
    normalized_portal = portal.strip().lower()

    if normalized_portal not in SUPPORTED_PORTALS:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported portal",
                "supported_portals": sorted(SUPPORTED_PORTALS),
            },
        )

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail="Portal import must be a CSV or JSON file.",
        )

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as handle:
            handle.write(payload)
            temporary_path = Path(handle.name)

        jobs = load_portal_file(
            portal=normalized_portal,
            path=temporary_path,
        )

        result = persist_broad_jobs(
            session=session,
            fetched_jobs=jobs,
        )
        session.commit()

    except PortalImportError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        session.rollback()
        raise
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return {
        "portal": normalized_portal,
        "filename": file.filename,
        "valid_rows": len(jobs),
        "new_jobs": result.new,
        "matched_existing": result.matched_existing,
        "existing_source": result.existing_source,
        "raw_payloads_saved": result.raw_saved,
    }


@router.post("/integrations/hiring-post/extract")
def hiring_post_extract(payload: HiringPostRequest) -> dict:
    return extract_hiring_post(
        payload.text,
        payload.source_url,
    )
