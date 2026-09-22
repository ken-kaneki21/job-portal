from types import SimpleNamespace

from jobintel.application_ops.answer_bank import (
    build_answer_bank,
)
from jobintel.application_ops.readiness import (
    readiness_payload,
)
from jobintel.application_ops.workday_assist import (
    build_workday_suggestions,
)


def build_profile():
    return SimpleNamespace(
        identity=SimpleNamespace(
            full_name="Test Candidate",
            email="test@example.com",
            phone="9999999999",
            location="Bengaluru",
            linkedin_url=("https://linkedin.com/in/test"),
            github_url=("https://github.com/test"),
            portfolio_url=None,
        ),
        preferences=SimpleNamespace(
            notice_period_days=60,
            expected_compensation=None,
        ),
        total_experience_years=2.2,
        source_resume_filename="resume.pdf",
        experience=[
            SimpleNamespace(
                company="Current Co",
                title="Data Engineer",
                end_date="present",
            )
        ],
    )


def test_answer_bank_uses_profile_and_target():
    answers = build_answer_bank(
        build_profile(),
        company="Target Co",
        title="Senior Data Engineer",
    )

    assert answers["first_name"].value == "Test"
    assert answers["last_name"].value == "Candidate"
    assert answers["notice_period_days"].value == 60
    assert "Target Co" in str(answers["why_company"].value)


def test_workday_suggestions_never_submit():
    answers = build_answer_bank(build_profile())

    suggestions = build_workday_suggestions(answers)

    keys = {item.key for item in suggestions}

    assert "email" in keys
    assert "phone" in keys


def test_readiness_has_no_blockers_when_core_fields_exist():
    profile = build_profile()

    job = SimpleNamespace(
        company="Target Co",
        title="Data Engineer",
        apply_url="https://example.com/apply",
    )

    payload = readiness_payload(
        profile=profile,
        job=job,
    )

    assert payload["ready_for_review"] is True
    assert payload["auto_submit_allowed"] is False
    assert payload["blocking_issues"] == []
