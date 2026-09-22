import os

from sqlalchemy import func, select

from jobintel.db.models import (
    JobApplicationStateRecord,
    JobRankingRecord,
    JobRecord,
)
from jobintel.db.session import SessionLocal
from jobintel.profile.runtime import ACTIVE_PROFILE_NAME

PROFILE_NAME = ACTIVE_PROFILE_NAME

HIGH_CONFIDENCE_LIMIT = 10
DISCOVERY_LIMIT = 15
STRETCH_LIMIT = 5


def get_ranking_run_id(
    session,
) -> int | None:
    """
    During a pipeline run, use that exact pipeline run.

    When run manually, use the latest historical
    pipeline ranking snapshot.
    """

    value = os.getenv("JOBINTEL_PIPELINE_RUN_ID")

    if value:
        return int(value)

    return session.scalar(
        select(func.max(JobRankingRecord.pipeline_run_id))
        .where(JobRankingRecord.profile_name == PROFILE_NAME)
        .where(JobRankingRecord.pipeline_run_id.is_not(None))
    )


def load_bucket(
    session,
    pipeline_run_id: int,
    bucket: str,
    limit: int,
):
    stmt = (
        select(
            JobRecord.id,
            JobRecord.title,
            JobRecord.company,
            JobRecord.location,
            JobRecord.apply_url,
            JobRankingRecord.score,
            JobRankingRecord.rank_position,
            JobApplicationStateRecord.status,
        )
        .join(
            JobRankingRecord,
            JobRankingRecord.job_id == JobRecord.id,
        )
        .outerjoin(
            JobApplicationStateRecord,
            (JobApplicationStateRecord.job_id == JobRecord.id)
            & (JobApplicationStateRecord.profile_name == PROFILE_NAME),
        )
        .where(JobRankingRecord.profile_name == PROFILE_NAME)
        .where(JobRankingRecord.pipeline_run_id == pipeline_run_id)
        .where(JobRankingRecord.bucket == bucket)
        .where(
            (JobApplicationStateRecord.status.is_(None))
            | (JobApplicationStateRecord.status == "new")
        )
        .order_by(
            JobRankingRecord.score.desc(),
            JobRankingRecord.rank_position.asc(),
        )
        .limit(limit)
    )

    return session.execute(stmt).all()


def print_bucket(
    title: str,
    rows,
) -> None:
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)

    if not rows:
        print()
        print("No new jobs.")
        return

    for index, row in enumerate(
        rows,
        start=1,
    ):
        print()

        print(f"#{index} | Job ID: {row.id}")

        print(row.title)

        print(f"{row.company} | {row.location or 'Unknown'}")

        print(f"Score: {row.score:.1f}")

        print(f"Apply: {row.apply_url}")

        print("-" * 100)


def main() -> None:
    with SessionLocal() as session:
        pipeline_run_id = get_ranking_run_id(session)

        if pipeline_run_id is None:
            print("No historical pipeline ranking snapshot found.")
            return

        high_confidence = load_bucket(
            session=session,
            pipeline_run_id=pipeline_run_id,
            bucket="high_confidence",
            limit=HIGH_CONFIDENCE_LIMIT,
        )

        discovery = load_bucket(
            session=session,
            pipeline_run_id=pipeline_run_id,
            bucket="discovery",
            limit=DISCOVERY_LIMIT,
        )

        stretch = load_bucket(
            session=session,
            pipeline_run_id=pipeline_run_id,
            bucket="stretch",
            limit=STRETCH_LIMIT,
        )

    total = len(high_confidence) + len(discovery) + len(stretch)

    print()
    print("=" * 100)
    print("DAILY JOB SHORTLIST")
    print("=" * 100)

    print(f"Profile: {PROFILE_NAME}")

    print(f"Ranking run: {pipeline_run_id}")

    print(f"New jobs selected: {total}")

    print(f"High confidence: {len(high_confidence)}")

    print(f"Discovery:       {len(discovery)}")

    print(f"Stretch:         {len(stretch)}")

    print_bucket(
        "HIGH CONFIDENCE",
        high_confidence,
    )

    print_bucket(
        "DISCOVERY",
        discovery,
    )

    print_bucket(
        "STRETCH",
        stretch,
    )


if __name__ == "__main__":
    main()
