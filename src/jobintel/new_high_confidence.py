import os

from sqlalchemy import select

from jobintel.db.models import (
    JobRankingRecord,
    JobRecord,
    PipelineRunRecord,
)
from jobintel.db.session import SessionLocal
from jobintel.profile.runtime import ACTIVE_PROFILE_NAME

PROFILE_NAME = ACTIVE_PROFILE_NAME
BUCKET = "high_confidence"


def get_recent_successful_ranking_runs(
    session,
) -> list[int]:
    """
    During an active pipeline:
        current pipeline run + previous successful run.

    During a manual invocation:
        two most recent successful runs.
    """

    current_run_value = os.getenv("JOBINTEL_PIPELINE_RUN_ID")

    # -------------------------------------------------
    # Running from inside pipeline
    # -------------------------------------------------

    if current_run_value:
        current_run_id = int(current_run_value)

        # Confirm the current run actually has rankings.
        current_has_rankings = session.scalar(
            select(JobRankingRecord.id)
            .where(JobRankingRecord.pipeline_run_id == current_run_id)
            .where(JobRankingRecord.profile_name == PROFILE_NAME)
            .limit(1)
        )

        if current_has_rankings is None:
            return []

        previous_run_id = session.scalar(
            select(PipelineRunRecord.id)
            .where(PipelineRunRecord.success.is_(True))
            .where(PipelineRunRecord.id < current_run_id)
            .where(
                PipelineRunRecord.id.in_(
                    select(JobRankingRecord.pipeline_run_id)
                    .where(JobRankingRecord.profile_name == PROFILE_NAME)
                    .where(JobRankingRecord.pipeline_run_id.is_not(None))
                )
            )
            .order_by(PipelineRunRecord.id.desc())
            .limit(1)
        )

        if previous_run_id is None:
            return [current_run_id]

        return [
            current_run_id,
            previous_run_id,
        ]

    # -------------------------------------------------
    # Manual invocation
    # -------------------------------------------------

    run_ids = session.scalars(
        select(PipelineRunRecord.id)
        .where(PipelineRunRecord.success.is_(True))
        .where(
            PipelineRunRecord.id.in_(
                select(JobRankingRecord.pipeline_run_id)
                .where(JobRankingRecord.profile_name == PROFILE_NAME)
                .where(JobRankingRecord.pipeline_run_id.is_not(None))
            )
        )
        .order_by(PipelineRunRecord.id.desc())
        .limit(2)
    ).all()

    return list(run_ids)


def get_high_confidence_job_ids(
    session,
    run_id: int,
) -> set[int]:
    job_ids = session.scalars(
        select(JobRankingRecord.job_id)
        .where(JobRankingRecord.profile_name == PROFILE_NAME)
        .where(JobRankingRecord.pipeline_run_id == run_id)
        .where(JobRankingRecord.bucket == BUCKET)
    ).all()

    return set(job_ids)


def main() -> None:
    with SessionLocal() as session:
        run_ids = get_recent_successful_ranking_runs(session)

        if len(run_ids) < 2:
            print()
            print("Need at least two ranking runs for comparison.")

            if run_ids:
                print(f"Current ranking run: {run_ids[0]}")

            return

        latest_run_id = run_ids[0]
        previous_run_id = run_ids[1]

        latest_ids = get_high_confidence_job_ids(
            session=session,
            run_id=latest_run_id,
        )

        previous_ids = get_high_confidence_job_ids(
            session=session,
            run_id=previous_run_id,
        )

        new_job_ids = latest_ids - previous_ids

        print()
        print("=" * 100)
        print("NEW HIGH-CONFIDENCE JOBS")
        print("=" * 100)

        print(f"Previous run: {previous_run_id}")

        print(f"Latest run:   {latest_run_id}")

        print(f"Previous high confidence: {len(previous_ids)}")

        print(f"Latest high confidence:   {len(latest_ids)}")

        print(f"New high confidence:      {len(new_job_ids)}")

        if not new_job_ids:
            print()
            print("No new high-confidence jobs.")
            return

        rows = session.execute(
            select(
                JobRecord.id,
                JobRecord.title,
                JobRecord.company,
                JobRecord.location,
                JobRecord.apply_url,
                JobRankingRecord.score,
            )
            .join(
                JobRankingRecord,
                JobRankingRecord.job_id == JobRecord.id,
            )
            .where(JobRankingRecord.pipeline_run_id == latest_run_id)
            .where(JobRankingRecord.profile_name == PROFILE_NAME)
            .where(JobRankingRecord.bucket == BUCKET)
            .where(JobRecord.id.in_(new_job_ids))
            .order_by(JobRankingRecord.score.desc())
        ).all()

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


if __name__ == "__main__":
    main()
