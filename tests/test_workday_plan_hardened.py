from jobintel.application_workflow.packet import ApplicationPacket
from jobintel.application_workflow.workday import build_workday_plan


def test_workday_plan_includes_review_sensitive_fields():
    packet = ApplicationPacket(
        job_id=1,
        company="Acme",
        title="Data Engineer",
        location="Bengaluru",
        apply_url="https://example.com/apply",
        profile_name="universal",
        answers={
            "first_name": "Test",
            "last_name": "Candidate",
            "email": "test@example.com",
            "phone": "9999999999",
            "notice_period_days": 60,
            "expected_compensation": "review",
        },
        cover_note=None,
        resume_summary=None,
        skills_to_emphasize=[],
        missing_skills_warning=[],
    )

    plan = build_workday_plan(packet)
    by_key = {field.key: field for field in plan.fields}

    assert plan.submit_action_enabled is False
    assert by_key["notice_period"].review_required is True
    assert by_key["expected_compensation"].review_required is True
    assert by_key["expected_compensation"].sensitive is True
