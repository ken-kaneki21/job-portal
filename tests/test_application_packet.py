from datetime import UTC, datetime

from jobintel.application_workflow.packet import build_application_packet
from jobintel.db.models import JobRecord
from jobintel.profile.universal import (
    CandidateIdentity,
    UniversalCandidateProfile,
)


class FakeSession:
    def __init__(self, job):
        self.job = job

    def get(self, model, job_id):
        return self.job

    def scalar(self, statement):
        return None


def test_packet_is_review_only_without_assets():
    job = JobRecord(
        id=10,
        source="greenhouse",
        source_identifier="example",
        external_id="1",
        company="Example",
        title="Data Engineer",
        location="Bangalore",
        description="Build pipelines",
        department="Data",
        apply_url="https://example.com/job/1",
        fingerprint="a" * 64,
        canonical_key=None,
        is_active=True,
        closed_at=None,
        first_seen_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
    )

    profile = UniversalCandidateProfile(
        profile_name="universal",
        identity=CandidateIdentity(
            full_name="Jane Example",
            email="jane@example.com",
        ),
        summary="Data Engineer",
        core_skills=["Python", "SQL"],
    )

    packet = build_application_packet(
        session=FakeSession(job),
        job_id=10,
        profile=profile,
    )

    assert packet.review_required is True
    assert packet.auto_submit_allowed is False
    assert packet.resume_summary == "Data Engineer"
    assert packet.skills_to_emphasize == ["Python", "SQL"]
