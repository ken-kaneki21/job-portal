import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from jobintel.db.models import JobRankingRecord, JobRecord
from jobintel.db.ranking_repository import save_rankings
from jobintel.models.company import Company
from jobintel.profile.models import CandidateProfile
from jobintel.ranking.scoring import detect_min_experience, rank_job
from jobintel.sources.greenhouse import GreenhouseSource, clean_html, make_fingerprint


def test_public_and_synthetic_screening_cases_are_stable_on_replay():
    path = Path(__file__).resolve().parents[1] / "eval/experience_screening_v1.json"
    fixture = json.loads(path.read_text(encoding="utf-8"))
    profile = CandidateProfile(
        name="test",
        target_titles=["AI Engineer", "Data Engineer", "Python Backend Engineer"],
        adjacent_titles=[],
        exclude_titles=[],
        preferred_locations=["Bengaluru"],
        allowed_countries=["India"],
        blocked_location_terms=["United States"],
        core_skills=["Python", "SQL"],
        secondary_skills=[],
        max_preferred_experience_years=3,
        hard_max_experience_years=fixture["candidate_hard_max_years"],
    )
    for case in fixture["cases"]:
        job = JobRecord(
            title=case["title"],
            location=case["location"],
            description=case["description"],
            first_seen_at=datetime.now(UTC),
            apply_url="https://example.invalid/job",
        )
        for _ in range(2):
            result = rank_job(job, profile)
            assert result.eligible is case["eligible"], case["id"]
            assert result.detected_experience == case["expected_years"], case["id"]


def test_missing_or_alternative_experience_stays_unknown():
    assert detect_min_experience("") is None
    assert detect_min_experience("minimum experience: years ???") is None
    assert detect_min_experience("5 years of experience or a relevant degree") is None


def test_greenhouse_preserves_requirement_sections_and_fingerprint():
    raw = (
        "<h3>Required qualifications</h3>"
        "<p>2 years of experience required.</p>"
        "<h3>Preferred qualifications</h3>"
        "<p>At least 6 years of experience in Databricks.</p>"
    )
    clean = clean_html(raw)
    assert clean is not None and "\nPreferred qualifications\n" in clean
    assert detect_min_experience(clean) == 2
    assert make_fingerprint("Acme", "Data Engineer", None, clean) == make_fingerprint(
        "Acme", "Data Engineer", None, " ".join(clean.split())
    )


def test_greenhouse_to_persisted_rankings_survives_reopen_and_replay(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'screening.sqlite'}")
    JobRecord.__table__.create(engine)
    JobRankingRecord.__table__.create(engine)
    profile = CandidateProfile(
        name="screening",
        target_titles=["Data Engineer"],
        adjacent_titles=[],
        exclude_titles=[],
        preferred_locations=["Bengaluru"],
        allowed_countries=["India"],
        blocked_location_terms=[],
        core_skills=["Python"],
        secondary_skills=[],
        max_preferred_experience_years=3,
        hard_max_experience_years=4,
    )
    company = Company(name="Example", ats="greenhouse", identifier="example")
    with Session(engine) as session:
        for job_id, content in enumerate(
            (
                "<p>Experience: 2–5 years</p><p>Minimum 5 years of experience required</p>",
                "<p>Minimum 2 years of experience</p><h3>Preferred qualifications</h3>"
                "<p>At least 6 years of experience with Spark</p>",
            ),
            start=1,
        ):
            source = GreenhouseSource._normalize(
                raw={
                    "id": job_id,
                    "title": "Data Engineer",
                    "absolute_url": f"https://example.invalid/jobs/{job_id}",
                    "location": {"name": "Bengaluru"},
                    "content": content,
                },
                company=company,
            )
            session.add(
                JobRecord(
                    **source.model_dump(
                        mode="json",
                        include={
                            "source",
                            "source_identifier",
                            "external_id",
                            "title",
                            "company",
                            "location",
                            "description",
                            "apply_url",
                            "fingerprint",
                        },
                    ),
                    first_seen_at=datetime.now(UTC),
                )
            )
        session.commit()

    for _ in range(2):
        engine.dispose()
        with Session(engine) as session:
            jobs = session.scalars(select(JobRecord).order_by(JobRecord.id)).all()
            for job in jobs:
                # SQLite strips offsets. The synthetic rows above were written in UTC.
                job.first_seen_at = job.first_seen_at.replace(tzinfo=UTC)
            ranked = [rank_job(job, profile) for job in jobs]
            assert [result.eligible for result in ranked] == [False, True]
            assert (
                save_rankings(
                    session=session,
                    profile_name=profile.name,
                    high_confidence=[],
                    discovery=[result for result in ranked if result.eligible],
                    stretch=[],
                )
                == 1
            )
            session.commit()
        with Session(engine) as session:
            rows = session.scalars(select(JobRankingRecord)).all()
            assert [(row.job_id, row.bucket) for row in rows] == [(2, "discovery")]
    engine.dispose()
