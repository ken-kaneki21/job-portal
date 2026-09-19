import hashlib
import json

from sqlalchemy import select

from jobintel.application_assets.generator import (
    GENERATOR_VERSION,
    generate_application_assets,
)
from jobintel.db.models import (
    JobApplicationAssetRecord,
    JobEnrichmentRecord,
    JobGapAnalysisRecord,
    JobRankingRecord,
    JobRecord,
)
from jobintel.db.session import (
    SessionLocal,
)
from jobintel.profile.loader import (
    load_profile,
)


PROFILE_PATH = "profiles/data_engineer.json"

PROFILE_NAME = "data_engineer"

MAX_JOBS = 100


def build_content_hash(
    *,
    job,
    enrichment,
    gap,
    ranking,
) -> str:
    payload = {
        "generator_version": (
            GENERATOR_VERSION
        ),
        "job_id": (
            job.id
        ),
        "job_title": (
            job.title
        ),
        "company": (
            job.company
        ),
        "enrichment_hash": (
            enrichment.content_hash
        ),
        "gap_hash": (
            gap.content_hash
        ),
        "ranking_score": (
            ranking.score
        ),
        "bucket": (
            ranking.bucket
        ),
    }

    raw = json.dumps(
        payload,
        sort_keys=True,
        default=str,
    )

    return hashlib.sha256(
        raw.encode(
            "utf-8"
        )
    ).hexdigest()


def load_latest_rankings(
    session,
) -> list[
    JobRankingRecord
]:
    """
    Use the most recent ranking row for each job/profile.

    We avoid depending on whether ranking was executed
    standalone or as part of a pipeline run.
    """

    rows = session.scalars(
        select(
            JobRankingRecord
        )
        .where(
            JobRankingRecord.profile_name
            == PROFILE_NAME
        )
        .order_by(
            JobRankingRecord.ranked_at.desc(),
            JobRankingRecord.id.desc(),
        )
    ).all()

    latest_by_job: dict[
        int,
        JobRankingRecord,
    ] = {}

    for row in rows:
        if row.job_id in latest_by_job:
            continue

        latest_by_job[
            row.job_id
        ] = row

    result = list(
        latest_by_job.values()
    )

    bucket_priority = {
        "high_confidence": 0,
        "discovery": 1,
        "stretch": 2,
    }

    result.sort(
        key=lambda row: (
            bucket_priority.get(
                row.bucket,
                99,
            ),
            -float(
                row.score
            ),
        )
    )

    return result[
        :MAX_JOBS
    ]


def main() -> None:
    profile = load_profile(
        PROFILE_PATH
    )

    inserted = 0
    updated = 0
    skipped = 0
    failed = 0

    with SessionLocal() as session:
        rankings = (
            load_latest_rankings(
                session
            )
        )

        print()
        print("=" * 100)
        print(
            "APPLICATION ASSET GENERATION"
        )
        print("=" * 100)

        print(
            f"Profile: {profile.name}"
        )

        print(
            f"Ranked jobs selected: "
            f"{len(rankings)}"
        )

        for index, ranking in enumerate(
            rankings,
            start=1,
        ):
            try:
                job = session.get(
                    JobRecord,
                    ranking.job_id,
                )

                if (
                    job is None
                    or not job.is_active
                ):
                    skipped += 1
                    continue

                enrichment = session.scalar(
                    select(
                        JobEnrichmentRecord
                    )
                    .where(
                        JobEnrichmentRecord.job_id
                        == job.id
                    )
                )

                gap = session.scalar(
                    select(
                        JobGapAnalysisRecord
                    )
                    .where(
                        JobGapAnalysisRecord.job_id
                        == job.id
                    )
                    .where(
                        JobGapAnalysisRecord.profile_name
                        == profile.name
                    )
                )

                if (
                    enrichment is None
                    or gap is None
                ):
                    skipped += 1
                    continue

                content_hash = (
                    build_content_hash(
                        job=job,
                        enrichment=enrichment,
                        gap=gap,
                        ranking=ranking,
                    )
                )

                existing = session.scalar(
                    select(
                        JobApplicationAssetRecord
                    )
                    .where(
                        JobApplicationAssetRecord.job_id
                        == job.id
                    )
                    .where(
                        JobApplicationAssetRecord.profile_name
                        == profile.name
                    )
                )

                if (
                    existing is not None
                    and existing.content_hash
                    == content_hash
                    and existing.generator_version
                    == GENERATOR_VERSION
                ):
                    skipped += 1
                    continue

                assets = (
                    generate_application_assets(
                        profile=profile,
                        job=job,
                        enrichment=enrichment,
                        gap=gap,
                        ranking=ranking,
                    )
                )

                payload = (
                    assets.to_dict()
                )

                if existing is None:
                    existing = (
                        JobApplicationAssetRecord(
                            job_id=job.id,
                            profile_name=(
                                profile.name
                            ),
                            generator_version=(
                                GENERATOR_VERSION
                            ),
                            content_hash=(
                                content_hash
                            ),
                            recruiter_dm=(
                                assets.recruiter_dm
                            ),
                            email_subject=(
                                assets.email_subject
                            ),
                            email_body=(
                                assets.email_body
                            ),
                            cover_note=(
                                assets.cover_note
                            ),
                            resume_summary=(
                                assets.resume_summary
                            ),
                            skills_to_emphasize=(
                                assets.skills_to_emphasize
                            ),
                            missing_skills_warning=(
                                assets.missing_skills_warning
                            ),
                            resume_bullets_to_emphasize=(
                                assets.resume_bullets_to_emphasize
                            ),
                            interview_talking_points=(
                                assets.interview_talking_points
                            ),
                            generated_payload=(
                                payload
                            ),
                        )
                    )

                    session.add(
                        existing
                    )

                    inserted += 1

                else:
                    existing.generator_version = (
                        GENERATOR_VERSION
                    )

                    existing.content_hash = (
                        content_hash
                    )

                    existing.recruiter_dm = (
                        assets.recruiter_dm
                    )

                    existing.email_subject = (
                        assets.email_subject
                    )

                    existing.email_body = (
                        assets.email_body
                    )

                    existing.cover_note = (
                        assets.cover_note
                    )

                    existing.resume_summary = (
                        assets.resume_summary
                    )

                    existing.skills_to_emphasize = (
                        assets.skills_to_emphasize
                    )

                    existing.missing_skills_warning = (
                        assets.missing_skills_warning
                    )

                    existing.resume_bullets_to_emphasize = (
                        assets.resume_bullets_to_emphasize
                    )

                    existing.interview_talking_points = (
                        assets.interview_talking_points
                    )

                    existing.generated_payload = (
                        payload
                    )

                    updated += 1

                if index % 25 == 0:
                    session.commit()

                    print(
                        f"Processed "
                        f"{index}/"
                        f"{len(rankings)}"
                    )

            except Exception as exc:
                session.rollback()

                failed += 1

                print(
                    f"FAILED job "
                    f"{ranking.job_id}: "
                    f"{exc}"
                )

        session.commit()

    print()
    print("=" * 100)
    print(
        "APPLICATION ASSET SUMMARY"
    )
    print("=" * 100)

    print(
        f"Inserted: {inserted}"
    )

    print(
        f"Updated:  {updated}"
    )

    print(
        f"Skipped:  {skipped}"
    )

    print(
        f"Failed:   {failed}"
    )


if __name__ == "__main__":
    main()