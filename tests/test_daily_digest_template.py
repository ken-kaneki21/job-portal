from jobintel.notifications.templates import (
    build_daily_digest_email,
)


def test_daily_digest_email_contains_ranked_jobs():
    subject, html = build_daily_digest_email(
        jobs=[
            {
                "title": "Data Engineer",
                "company": "Example",
                "location": "Bengaluru",
                "apply_url": "https://example.com/jobs/1",
                "score": 82.5,
                "bucket": "high_confidence",
            }
        ],
        pipeline_run_id=29,
    )

    assert "run 29" in subject
    assert "Data Engineer" in html
    assert "82.5" in html
    assert "Open job" in html
