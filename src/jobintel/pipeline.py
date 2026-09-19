import os
import subprocess
import sys
from datetime import datetime, timezone

from sqlalchemy import func, select

from jobintel.db.models import (
    JobRankingRecord,
    JobRecord,
    PipelineRunRecord,
    ScanRecord,
)
from jobintel.db.session import SessionLocal


STEPS = [
    (
        "Direct ATS ingestion",
        "jobintel.main",
    ),
    (
        "Broad search",
        "jobintel.broad_search",
    ),
    (
        "Queue company discovery candidates",
        "jobintel.enqueue_company_discovery",
    ),
    (
        "Resolve company ATS",
        "jobintel.resolve_company_discovery",
    ),
    (
        "JD enrichment",
        "jobintel.backfill_enrichments",
    ),
    (
        "Refresh job embeddings",
        "jobintel.backfill_embeddings",
    ),
    (
        "Candidate JD gap analysis",
        "jobintel.backfill_gap_analysis",
    ),
    (
        "Ranking",
        "jobintel.rank",
    ),
    (
        "Generate application assets",
        "jobintel.backfill_application_assets",
    ),
    (
        "Daily shortlist",
        "jobintel.shortlist",
    ),
    (
        "New high-confidence jobs",
        "jobintel.new_high_confidence",
    ),
    (
        "Queue notifications",
        "jobintel.enqueue_notifications",
    ),
    (
        "Data quality checks",
        "jobintel.quality_checks",
    ),
    (
        "Retry failed notifications",
        "jobintel.retry_notifications",
    ),
    (
        "Deliver notifications",
        "jobintel.deliver_notifications",
    ),
]


def run_step(
    label: str,
    module: str,
    run_id: int,
) -> None:
    print()
    print("=" * 100)
    print(label)
    print("=" * 100)

    env = os.environ.copy()

    env[
        "JOBINTEL_PIPELINE_RUN_ID"
    ] = str(
        run_id
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            module,
        ],
        check=False,
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{label} failed "
            f"with exit code "
            f"{result.returncode}"
        )


def create_pipeline_run() -> int:
    with SessionLocal() as session:
        record = PipelineRunRecord(
            started_at=datetime.now(
                timezone.utc
            ),
            success=False,
        )

        session.add(
            record
        )

        session.commit()

        session.refresh(
            record
        )

        return record.id


def finalize_pipeline_run(
    run_id: int,
    success: bool,
    error_message: str | None = None,
) -> None:
    with SessionLocal() as session:
        record = session.get(
            PipelineRunRecord,
            run_id,
        )

        if record is None:
            return

        # ---------------------------------------------
        # Jobs fetched during this pipeline run
        # ---------------------------------------------

        jobs_fetched = session.scalar(
            select(
                func.coalesce(
                    func.sum(
                        ScanRecord.jobs_fetched
                    ),
                    0,
                )
            )
            .where(
                ScanRecord.started_at
                >= record.started_at
            )
        )

        # ---------------------------------------------
        # Current active jobs
        # ---------------------------------------------

        active_jobs = session.scalar(
            select(
                func.count()
            )
            .select_from(
                JobRecord
            )
            .where(
                JobRecord.is_active.is_(
                    True
                )
            )
        )

        # ---------------------------------------------
        # Ranking records created for THIS run only
        # ---------------------------------------------

        rankings_persisted = session.scalar(
            select(
                func.count()
            )
            .select_from(
                JobRankingRecord
            )
            .where(
                JobRankingRecord.profile_name
                == "data_engineer"
            )
            .where(
                JobRankingRecord.pipeline_run_id
                == run_id
            )
        )

        record.finished_at = (
            datetime.now(
                timezone.utc
            )
        )

        record.success = (
            success
        )

        record.jobs_fetched = int(
            jobs_fetched or 0
        )

        record.active_jobs = int(
            active_jobs or 0
        )

        record.eligible_jobs = int(
            rankings_persisted or 0
        )

        record.rankings_persisted = int(
            rankings_persisted or 0
        )

        record.error_message = (
            error_message
        )

        session.commit()


def main() -> None:
    print()
    print("=" * 100)
    print(
        "JOB INTELLIGENCE PIPELINE"
    )
    print("=" * 100)

    run_id = (
        create_pipeline_run()
    )

    try:
        for (
            label,
            module,
        ) in STEPS:
            run_step(
                label=label,
                module=module,
                run_id=run_id,
            )

        finalize_pipeline_run(
            run_id=run_id,
            success=True,
        )

    except Exception as exc:
        finalize_pipeline_run(
            run_id=run_id,
            success=False,
            error_message=str(
                exc
            ),
        )

        print()
        print("=" * 100)
        print(
            "PIPELINE FAILED"
        )
        print("=" * 100)

        print(
            f"Error: {exc}"
        )

        raise

    print()
    print("=" * 100)
    print(
        "PIPELINE COMPLETE"
    )
    print("=" * 100)

    print(
        f"Pipeline run ID: "
        f"{run_id}"
    )


if __name__ == "__main__":
    main()