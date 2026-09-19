from sqlalchemy import delete

from jobintel.db.models import (
    JobRankingRecord,
)


def add_bucket_rankings(
    *,
    session,
    profile_name: str,
    bucket: str,
    results: list,
    pipeline_run_id: int | None,
) -> int:
    inserted = 0

    for position, result in enumerate(
        results,
        start=1,
    ):
        record = JobRankingRecord(
            job_id=result.job.id,
            profile_name=profile_name,
            bucket=bucket,
            score=result.score,
            deterministic_score=(
                result.deterministic_score
            ),
            semantic_score=(
                result.semantic_score
            ),
            gap_score=(
                result.gap_score
            ),
            rank_position=position,
            pipeline_run_id=(
                pipeline_run_id
            ),
        )

        session.add(
            record
        )

        inserted += 1

    return inserted


def clear_existing_snapshot(
    *,
    session,
    profile_name: str,
    pipeline_run_id: int | None,
) -> None:
    """
    Make saving a ranking snapshot idempotent.

    Pipeline run:
        Replace rows belonging to this exact run.

    Standalone rank command:
        Replace rows with pipeline_run_id IS NULL.

    Historical pipeline snapshots remain untouched.
    """

    stmt = delete(
        JobRankingRecord
    ).where(
        JobRankingRecord.profile_name
        == profile_name
    )

    if pipeline_run_id is None:
        stmt = stmt.where(
            JobRankingRecord.pipeline_run_id
            .is_(None)
        )

    else:
        stmt = stmt.where(
            JobRankingRecord.pipeline_run_id
            == pipeline_run_id
        )

    session.execute(
        stmt
    )


def save_rankings(
    *,
    session,
    profile_name: str,
    high_confidence: list,
    discovery: list,
    stretch: list,
    pipeline_run_id: int | None = None,
) -> int:
    """
    Persist one complete ranking snapshot.

    Returns:
        Number of ranking rows persisted.
    """

    clear_existing_snapshot(
        session=session,
        profile_name=profile_name,
        pipeline_run_id=(
            pipeline_run_id
        ),
    )

    inserted = 0

    inserted += add_bucket_rankings(
        session=session,
        profile_name=profile_name,
        bucket="high_confidence",
        results=high_confidence,
        pipeline_run_id=(
            pipeline_run_id
        ),
    )

    inserted += add_bucket_rankings(
        session=session,
        profile_name=profile_name,
        bucket="discovery",
        results=discovery,
        pipeline_run_id=(
            pipeline_run_id
        ),
    )

    inserted += add_bucket_rankings(
        session=session,
        profile_name=profile_name,
        bucket="stretch",
        results=stretch,
        pipeline_run_id=(
            pipeline_run_id
        ),
    )

    return inserted