from jobintel.application_workflow.answers import (
    build_application_answers,
    split_name,
)
from jobintel.profile.universal import (
    CandidateIdentity,
    CandidatePreferences,
    ExperienceEntry,
    UniversalCandidateProfile,
)


def test_split_name():
    assert split_name("Jane Example Doe") == ("Jane", "Example Doe")


def test_application_answers_use_structured_profile():
    profile = UniversalCandidateProfile(
        profile_name="universal",
        identity=CandidateIdentity(
            full_name="Jane Example",
            email="jane@example.com",
            location="Bangalore",
            linkedin_url="https://linkedin.com/in/example",
        ),
        total_experience_years=2.5,
        experience=[
            ExperienceEntry(
                company="Example Co",
                title="Data Engineer",
                start_date="2025",
                end_date="Present",
            )
        ],
        preferences=CandidatePreferences(
            notice_period_days=30,
            expected_compensation="20 LPA",
        ),
    )

    answers = build_application_answers(profile)

    assert answers.first_name == "Jane"
    assert answers.last_name == "Example"
    assert answers.current_company == "Example Co"
    assert answers.current_title == "Data Engineer"
    assert answers.total_experience_years == 2.5
    assert answers.notice_period_days == 30
