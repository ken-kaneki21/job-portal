from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from jobintel.db.models import (
    JobEmbeddingRecord,
    JobRankingRecord,
    JobRecord,
    ScanRecord,
)


def build_pipeline_quality_snapshot(
    *,
    session,
    run_id: int,
    started_at: datetime,
) -> dict:
    active_jobs = int(
        session.scalar(
            select(func.count())
            .select_from(JobRecord)
            .where(JobRecord.is_active.is_(True))
        )
        or 0
    )
    ranked_jobs = int(
        session.scalar(
            select(func.count(func.distinct(JobRankingRecord.job_id))).where(
                JobRankingRecord.pipeline_run_id == run_id
            )
        )
        or 0
    )
    embedded_jobs = int(
        session.scalar(
            select(func.count(func.distinct(JobEmbeddingRecord.job_id)))
            .join(JobRecord, JobRecord.id == JobEmbeddingRecord.job_id)
            .where(JobRecord.is_active.is_(True))
        )
        or 0
    )
    failed_scans = int(
        session.scalar(
            select(func.count())
            .select_from(ScanRecord)
            .where(ScanRecord.started_at >= started_at)
            .where(ScanRecord.success.is_(False))
        )
        or 0
    )
    stale_cutoff = datetime.now(UTC) - timedelta(days=30)
    stale_jobs = int(
        session.scalar(
            select(func.count())
            .select_from(JobRecord)
            .where(JobRecord.is_active.is_(True))
            .where(JobRecord.last_seen_at < stale_cutoff)
        )
        or 0
    )

    embedding_coverage = embedded_jobs / active_jobs if active_jobs else 0.0
    ranking_coverage = ranked_jobs / active_jobs if active_jobs else 0.0
    checks = {
        "active_jobs_present": active_jobs > 0,
        "scan_failures_clear": failed_scans == 0,
        "freshness": stale_jobs == 0,
        "embedding_coverage": embedding_coverage >= 0.95,
        "ranking_coverage": ranking_coverage >= 0.40,
    }
    return {
        "captured_at": datetime.now(UTC).isoformat(),
        "active_jobs": active_jobs,
        "ranked_jobs": ranked_jobs,
        "embedded_jobs": embedded_jobs,
        "failed_scans": failed_scans,
        "stale_jobs": stale_jobs,
        "embedding_coverage": round(embedding_coverage, 4),
        "ranking_coverage": round(ranking_coverage, 4),
        "checks": checks,
        "passed": all(checks.values()),
    }
