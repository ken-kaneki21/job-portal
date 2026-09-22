import json

from jobintel.search_sources.portal_import import inspect_portal_file


def test_portal_import_reports_invalid_and_duplicate_rows(tmp_path):
    path = tmp_path / "jobs.csv"
    path.write_text(
        (
            "Job Title,Company Name,Job URL,Location\n"
            "Data Engineer,Acme,https://example.com/jobs/1,Bengaluru\n"
            "Data Engineer,Acme,https://example.com/jobs/1,Bengaluru\n"
            "Missing URL,Acme,,Bengaluru\n"
        ),
        encoding="utf-8",
    )

    report = inspect_portal_file(portal="linkedin", path=path)

    assert report.total_rows == 3
    assert report.valid_rows == 1
    assert report.duplicate_rows == 1
    assert report.invalid_rows == 1
    assert report.jobs[0].job.company == "Acme"
    assert report.jobs[0].raw["import_provenance"]["row_number"] == 1


def test_portal_json_supports_data_wrapper(tmp_path):
    path = tmp_path / "jobs.json"
    path.write_text(
        json.dumps(
            {
                "data": [
                    {
                        "title": "Data Analyst",
                        "company": "Example",
                        "url": "https://example.com/job/2",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = inspect_portal_file(portal="indeed", path=path)

    assert report.valid_rows == 1
    assert report.invalid_rows == 0
    assert report.jobs[0].job.source == "indeed"
