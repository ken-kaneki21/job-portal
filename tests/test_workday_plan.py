from jobintel.application_workflow.packet import ApplicationPacket
from jobintel.application_workflow.workday import build_workday_plan


def test_workday_plan_requires_review_and_disables_submit():
    packet = ApplicationPacket(
        job_id=1,
        company="Example",
        title="Data Engineer",
        location="Bangalore",
        apply_url="https://example.workdayjobs.com/job/1",
        profile_name="universal",
        answers={
            "first_name": "Jane",
            "last_name": "Example",
            "email": "jane@example.com",
            "phone": None,
            "current_location": "Bangalore",
            "linkedin_url": "https://linkedin.com/in/example",
            "github_url": "https://github.com/example",
            "portfolio_url": None,
            "current_company": "Example Co",
            "current_title": "Data Engineer",
            "total_experience_years": 2.5,
            "notice_period_days": 30,
            "expected_compensation": None,
        },
        cover_note=None,
        resume_summary=None,
        skills_to_emphasize=[],
        missing_skills_warning=[],
    )

    plan = build_workday_plan(packet)

    assert plan.review_required is True
    assert plan.submit_action_enabled is False

    keys = {field.key for field in plan.fields}

    assert "email" in keys
    assert "linkedin" in keys
    assert "current_title" in keys
