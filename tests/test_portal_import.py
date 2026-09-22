from __future__ import annotations

import json

import pytest

from jobintel.search_sources.portal_import import (
    PortalImportError,
    load_portal_file,
    normalize_portal_job,
)


@pytest.mark.parametrize(
    "portal",
    ["linkedin", "naukri", "foundit", "indeed"],
)
def test_normalize_supported_portals(portal):
    fetched = normalize_portal_job(
        portal=portal,
        row={
            "job_title": "Data Engineer",
            "company_name": "Example",
            "job_location": "Bangalore",
            "job_url": "https://example.com/job/1",
            "job_description": "Python SQL Snowflake",
        },
    )

    assert fetched.job.source == portal
    assert fetched.job.title == "Data Engineer"
    assert fetched.raw["imported"] is True


def test_external_id_is_deterministic():
    row = {
        "title": "Data Engineer",
        "company": "Example",
        "url": "https://example.com/job/1",
    }

    first = normalize_portal_job(
        portal="linkedin",
        row=row,
    )

    second = normalize_portal_job(
        portal="linkedin",
        row=row,
    )

    assert first.job.external_id == second.job.external_id


def test_json_import(tmp_path):
    path = tmp_path / "jobs.json"

    path.write_text(
        json.dumps(
            [
                {
                    "title": "Data Engineer",
                    "company": "Example",
                    "url": "https://example.com/job/1",
                }
            ]
        ),
        encoding="utf-8",
    )

    jobs = load_portal_file(
        portal="indeed",
        path=path,
    )

    assert len(jobs) == 1


def test_unsupported_portal_rejected():
    with pytest.raises(PortalImportError):
        normalize_portal_job(
            portal="unknown",
            row={
                "title": "Data Engineer",
                "company": "Example",
                "url": "https://example.com/job",
            },
        )
