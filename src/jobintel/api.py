from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from pydantic import BaseModel, Field
from sqlalchemy import (
    func,
    select,
    text,
)
from sqlalchemy.orm import Session

from jobintel.api_application_assets import (
    router as application_assets_router,
)
from jobintel.api_application_workflow import (
    router as application_workflow_router,
)
from jobintel.api_outcomes import router as outcomes_router
from jobintel.api_profile import router as profile_router
from jobintel.api_temporal import (
    router as temporal_router,
)
from jobintel.api_temporal import (
    start_temporal_pipeline,
)
from jobintel.db.application_event_repository import (
    add_application_event,
    get_application_history,
)
from jobintel.db.models import (
    JobApplicationAssetRecord,
    JobApplicationStateRecord,
    JobEnrichmentRecord,
    JobGapAnalysisRecord,
    JobRankingRecord,
    JobRecord,
    PipelineRunRecord,
)
from jobintel.db.session import (
    SessionLocal,
)
from jobintel.observability import (
    CorrelationIdMiddleware,
    configure_logging,
    metrics_response,
)
from jobintel.profile.runtime import ACTIVE_PROFILE_NAME

DEFAULT_PROFILE = ACTIVE_PROFILE_NAME


VALID_JOB_STATUSES = {
    "new",
    "seen",
    "saved",
    "dismissed",
    "applied",
    "interviewing",
    "rejected",
    "offer",
}


configure_logging("jobintel-api")


app = FastAPI(
    title="Job Intelligence API",
    description=(
        "Private API for job discovery, "
        "ranking, gap analysis, application "
        "assets, application tracking, "
        "history, and pipeline observability."
    ),
    version="0.3.0",
)


app.include_router(application_assets_router)
app.include_router(application_workflow_router)
app.include_router(outcomes_router)
app.include_router(profile_router)


app.include_router(temporal_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(CorrelationIdMiddleware)


class JobStateRequest(BaseModel):
    status: str = Field(
        min_length=1,
        max_length=50,
    )

    notes: str | None = None


class NotesRequest(BaseModel):
    notes: str | None = None


def get_db():
    session = SessionLocal()

    try:
        yield session

    finally:
        session.close()


def json_safe(
    value: Any,
):
    if value is None:
        return None

    if isinstance(
        value,
        (
            datetime,
            date,
        ),
    ):
        return value.isoformat()

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): json_safe(nested_value)
            for (
                key,
                nested_value,
            ) in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        return [json_safe(item) for item in value]

    return str(value)


def serialize_model(
    record,
) -> dict:
    if record is None:
        return {}

    return {
        column.name: json_safe(
            getattr(
                record,
                column.name,
            )
        )
        for column in record.__table__.columns
    }


def compact_job(
    job: JobRecord,
) -> dict:
    return {
        "id": (job.id),
        "title": (job.title),
        "company": (job.company),
        "location": (job.location),
        "url": (job.apply_url),
        "is_active": (job.is_active),
        "posted_at": (json_safe(job.posted_at)),
        "first_seen_at": (json_safe(job.first_seen_at)),
        "last_seen_at": (json_safe(job.last_seen_at)),
    }


def require_job(
    session: Session,
    job_id: int,
) -> JobRecord:
    job = session.get(
        JobRecord,
        job_id,
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=("Job not found"),
        )

    return job


def latest_pipeline_ranking_run_id(
    session: Session,
) -> int | None:
    return session.scalar(
        select(func.max(JobRankingRecord.pipeline_run_id)).where(
            JobRankingRecord.pipeline_run_id.is_not(None)
        )
    )


def latest_ranking_for_job(
    session: Session,
    *,
    job_id: int,
    profile_name: str = DEFAULT_PROFILE,
) -> JobRankingRecord | None:
    return session.scalar(
        select(JobRankingRecord)
        .where(JobRankingRecord.job_id == job_id)
        .where(JobRankingRecord.profile_name == profile_name)
        .order_by(
            JobRankingRecord.ranked_at.desc(),
            JobRankingRecord.id.desc(),
        )
        .limit(1)
    )


def get_job_state_record(
    session: Session,
    *,
    job_id: int,
    profile_name: str,
) -> JobApplicationStateRecord | None:
    return session.scalar(
        select(JobApplicationStateRecord)
        .where(JobApplicationStateRecord.job_id == job_id)
        .where(JobApplicationStateRecord.profile_name == profile_name)
        .limit(1)
    )


def set_job_state(
    session: Session,
    *,
    job_id: int,
    profile_name: str,
    status: str,
    notes: str | None = None,
    source: str = "api",
) -> JobApplicationStateRecord:
    require_job(
        session,
        job_id,
    )

    normalized_status = status.strip().lower()

    if normalized_status not in VALID_JOB_STATUSES:
        raise HTTPException(
            status_code=400,
            detail={
                "message": ("Invalid job status"),
                "allowed_statuses": (sorted(VALID_JOB_STATUSES)),
            },
        )

    record = get_job_state_record(
        session,
        job_id=job_id,
        profile_name=profile_name,
    )

    if record is None:
        previous_status = "new"

        record = JobApplicationStateRecord(
            job_id=job_id,
            profile_name=(profile_name),
            status=(normalized_status),
            notes=notes,
        )

        session.add(record)

    else:
        previous_status = record.status

        record.status = normalized_status

        if notes is not None:
            record.notes = notes

    if previous_status != normalized_status:
        add_application_event(
            session=session,
            job_id=job_id,
            profile_name=(profile_name),
            previous_status=(previous_status),
            new_status=(normalized_status),
            notes=notes,
            source=source,
        )

    session.commit()

    session.refresh(record)

    return record


@app.get("/")
def root():
    return {
        "service": ("job-intelligence"),
        "version": ("0.3.0"),
        "docs": ("/docs"),
        "health": ("/health"),
    }


@app.get(
    "/metrics",
    include_in_schema=False,
)
def metrics():
    return metrics_response()


@app.get("/health")
def health(
    session: Session = Depends(get_db),
):
    try:
        session.execute(text("SELECT 1"))

        active_jobs = session.scalar(
            select(func.count())
            .select_from(JobRecord)
            .where(JobRecord.is_active.is_(True))
        )

        latest_run = session.scalar(
            select(PipelineRunRecord).order_by(PipelineRunRecord.id.desc()).limit(1)
        )

        return {
            "status": ("ok"),
            "database": ("connected"),
            "active_jobs": int(active_jobs or 0),
            "latest_pipeline_run": (
                serialize_model(latest_run) if latest_run else None
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(f"Database health check failed: {exc}"),
        ) from exc


@app.get("/jobs")
def list_jobs(
    active_only: bool = True,
    company: str | None = None,
    title: str | None = None,
    location: str | None = None,
    limit: int = Query(
        50,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
    session: Session = Depends(get_db),
):
    stmt = select(JobRecord)

    if active_only:
        stmt = stmt.where(JobRecord.is_active.is_(True))

    if company:
        stmt = stmt.where(func.lower(JobRecord.company).contains(company.lower()))

    if title:
        stmt = stmt.where(func.lower(JobRecord.title).contains(title.lower()))

    if location:
        stmt = stmt.where(func.lower(JobRecord.location).contains(location.lower()))

    stmt = stmt.order_by(JobRecord.id.desc()).offset(offset).limit(limit)

    jobs = session.scalars(stmt).all()

    return {
        "count": (len(jobs)),
        "offset": (offset),
        "limit": (limit),
        "jobs": [compact_job(job) for job in jobs],
    }


@app.get("/jobs/{job_id}")
def get_job(
    job_id: int,
    profile_name: str = DEFAULT_PROFILE,
    session: Session = Depends(get_db),
):
    job = require_job(
        session,
        job_id,
    )

    enrichment = session.scalar(
        select(JobEnrichmentRecord).where(JobEnrichmentRecord.job_id == job_id).limit(1)
    )

    gap = session.scalar(
        select(JobGapAnalysisRecord)
        .where(JobGapAnalysisRecord.job_id == job_id)
        .where(JobGapAnalysisRecord.profile_name == profile_name)
        .limit(1)
    )

    ranking = latest_ranking_for_job(
        session,
        job_id=job_id,
        profile_name=(profile_name),
    )

    asset = session.scalar(
        select(JobApplicationAssetRecord)
        .where(JobApplicationAssetRecord.job_id == job_id)
        .where(JobApplicationAssetRecord.profile_name == profile_name)
        .limit(1)
    )

    state = get_job_state_record(
        session,
        job_id=job_id,
        profile_name=(profile_name),
    )

    history = get_application_history(
        session=session,
        job_id=job_id,
        profile_name=(profile_name),
    )

    return {
        "job": (serialize_model(job)),
        "state": (
            serialize_model(state)
            if state
            else {
                "job_id": (job_id),
                "profile_name": (profile_name),
                "status": ("new"),
                "notes": (None),
            }
        ),
        "history": [serialize_model(event) for event in history],
        "enrichment": (serialize_model(enrichment) if enrichment else None),
        "gap_analysis": (serialize_model(gap) if gap else None),
        "ranking": (serialize_model(ranking) if ranking else None),
        "application_assets": (serialize_model(asset) if asset else None),
    }


@app.get("/rankings")
def get_rankings(
    profile_name: str = DEFAULT_PROFILE,
    bucket: str | None = None,
    pipeline_run_id: int | None = None,
    min_score: float | None = None,
    limit: int = Query(
        50,
        ge=1,
        le=500,
    ),
    session: Session = Depends(get_db),
):
    if pipeline_run_id is None:
        pipeline_run_id = latest_pipeline_ranking_run_id(session)

    stmt = (
        select(
            JobRankingRecord,
            JobRecord,
        )
        .join(
            JobRecord,
            JobRecord.id == JobRankingRecord.job_id,
        )
        .where(JobRankingRecord.profile_name == profile_name)
    )

    if pipeline_run_id is not None:
        stmt = stmt.where(JobRankingRecord.pipeline_run_id == pipeline_run_id)

    if bucket:
        stmt = stmt.where(JobRankingRecord.bucket == bucket)

    if min_score is not None:
        stmt = stmt.where(JobRankingRecord.score >= min_score)

    stmt = stmt.order_by(
        JobRankingRecord.score.desc(),
        JobRankingRecord.rank_position.asc(),
    ).limit(limit)

    rows = session.execute(stmt).all()

    return {
        "profile_name": (profile_name),
        "pipeline_run_id": (pipeline_run_id),
        "bucket": (bucket),
        "count": (len(rows)),
        "results": [
            {
                "ranking": (serialize_model(ranking)),
                "job": (compact_job(job)),
            }
            for (
                ranking,
                job,
            ) in rows
        ],
    }


@app.get("/rankings/stats")
def get_ranking_stats(
    profile_name: str = DEFAULT_PROFILE,
    pipeline_run_id: int | None = None,
    session: Session = Depends(get_db),
):
    if pipeline_run_id is None:
        pipeline_run_id = latest_pipeline_ranking_run_id(session)

    empty_buckets = {
        "high_confidence": 0,
        "discovery": 0,
        "stretch": 0,
    }

    if pipeline_run_id is None:
        return {
            "profile_name": profile_name,
            "pipeline_run_id": None,
            "total": 0,
            "buckets": empty_buckets,
        }

    total = session.scalar(
        select(func.count(JobRankingRecord.id))
        .where(JobRankingRecord.profile_name == profile_name)
        .where(JobRankingRecord.pipeline_run_id == pipeline_run_id)
    )

    bucket_rows = session.execute(
        select(
            JobRankingRecord.bucket,
            func.count(JobRankingRecord.id),
        )
        .where(JobRankingRecord.profile_name == profile_name)
        .where(JobRankingRecord.pipeline_run_id == pipeline_run_id)
        .group_by(JobRankingRecord.bucket)
    ).all()

    buckets = empty_buckets.copy()

    for bucket, count in bucket_rows:
        if bucket is None:
            continue

        buckets[str(bucket)] = int(count)

    return {
        "profile_name": profile_name,
        "pipeline_run_id": pipeline_run_id,
        "total": int(total or 0),
        "buckets": buckets,
    }


@app.get("/shortlist")
def get_shortlist(
    profile_name: str = DEFAULT_PROFILE,
    high_confidence_limit: int = Query(
        15,
        ge=1,
        le=100,
    ),
    discovery_limit: int = Query(
        15,
        ge=0,
        le=100,
    ),
    stretch_limit: int = Query(
        10,
        ge=0,
        le=100,
    ),
    session: Session = Depends(get_db),
):
    pipeline_run_id = latest_pipeline_ranking_run_id(session)

    if pipeline_run_id is None:
        return {
            "profile_name": (profile_name),
            "pipeline_run_id": (None),
            "high_confidence": [],
            "discovery": [],
            "stretch": [],
        }

    def load_bucket(
        bucket: str,
        limit: int,
    ):
        if limit <= 0:
            return []

        rows = session.execute(
            select(
                JobRankingRecord,
                JobRecord,
            )
            .join(
                JobRecord,
                JobRecord.id == JobRankingRecord.job_id,
            )
            .where(JobRankingRecord.profile_name == profile_name)
            .where(JobRankingRecord.pipeline_run_id == pipeline_run_id)
            .where(JobRankingRecord.bucket == bucket)
            .order_by(
                JobRankingRecord.score.desc(),
                JobRankingRecord.rank_position.asc(),
            )
            .limit(limit)
        ).all()

        return [
            {
                "job": (compact_job(job)),
                "ranking": (serialize_model(ranking)),
            }
            for (
                ranking,
                job,
            ) in rows
        ]

    return {
        "profile_name": (profile_name),
        "pipeline_run_id": (pipeline_run_id),
        "high_confidence": (
            load_bucket(
                "high_confidence",
                high_confidence_limit,
            )
        ),
        "discovery": (
            load_bucket(
                "discovery",
                discovery_limit,
            )
        ),
        "stretch": (
            load_bucket(
                "stretch",
                stretch_limit,
            )
        ),
    }


@app.get("/jobs/{job_id}/gap-analysis")
def get_gap_analysis(
    job_id: int,
    profile_name: str = DEFAULT_PROFILE,
    session: Session = Depends(get_db),
):
    job = require_job(
        session,
        job_id,
    )

    record = session.scalar(
        select(JobGapAnalysisRecord)
        .where(JobGapAnalysisRecord.job_id == job_id)
        .where(JobGapAnalysisRecord.profile_name == profile_name)
        .limit(1)
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=("Gap analysis not found for this job/profile"),
        )

    return {
        "job": (compact_job(job)),
        "gap_analysis": (serialize_model(record)),
    }


@app.get("/jobs/{job_id}/application-assets")
def get_application_assets(
    job_id: int,
    profile_name: str = DEFAULT_PROFILE,
    session: Session = Depends(get_db),
):
    job = require_job(
        session,
        job_id,
    )

    record = session.scalar(
        select(JobApplicationAssetRecord)
        .where(JobApplicationAssetRecord.job_id == job_id)
        .where(JobApplicationAssetRecord.profile_name == profile_name)
        .limit(1)
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=("Application assets not found for this job/profile"),
        )

    return {
        "job": (compact_job(job)),
        "application_assets": (serialize_model(record)),
    }


@app.get("/jobs/{job_id}/state")
def get_job_state(
    job_id: int,
    profile_name: str = DEFAULT_PROFILE,
    session: Session = Depends(get_db),
):
    job = require_job(
        session,
        job_id,
    )

    record = get_job_state_record(
        session,
        job_id=job_id,
        profile_name=(profile_name),
    )

    return {
        "job": (compact_job(job)),
        "state": (
            serialize_model(record)
            if record
            else {
                "job_id": (job_id),
                "profile_name": (profile_name),
                "status": ("new"),
                "notes": (None),
            }
        ),
    }


@app.get("/jobs/{job_id}/history")
def get_job_history(
    job_id: int,
    profile_name: str = DEFAULT_PROFILE,
    session: Session = Depends(get_db),
):
    job = require_job(
        session,
        job_id,
    )

    events = get_application_history(
        session=session,
        job_id=job_id,
        profile_name=(profile_name),
    )

    return {
        "job": (compact_job(job)),
        "profile_name": (profile_name),
        "count": (len(events)),
        "history": [serialize_model(event) for event in events],
    }


@app.post("/jobs/{job_id}/state")
def update_job_state(
    job_id: int,
    payload: JobStateRequest,
    profile_name: str = DEFAULT_PROFILE,
    session: Session = Depends(get_db),
):
    record = set_job_state(
        session,
        job_id=job_id,
        profile_name=(profile_name),
        status=(payload.status),
        notes=(payload.notes),
    )

    return {
        "message": ("Job state updated"),
        "state": (serialize_model(record)),
    }


@app.post("/jobs/{job_id}/save")
def save_job(
    job_id: int,
    payload: NotesRequest | None = None,
    profile_name: str = DEFAULT_PROFILE,
    session: Session = Depends(get_db),
):
    record = set_job_state(
        session,
        job_id=job_id,
        profile_name=(profile_name),
        status="saved",
        notes=(payload.notes if payload else None),
    )

    return {
        "message": ("Job saved"),
        "state": (serialize_model(record)),
    }


@app.post("/jobs/{job_id}/dismiss")
def dismiss_job(
    job_id: int,
    payload: NotesRequest | None = None,
    profile_name: str = DEFAULT_PROFILE,
    session: Session = Depends(get_db),
):
    record = set_job_state(
        session,
        job_id=job_id,
        profile_name=(profile_name),
        status="dismissed",
        notes=(payload.notes if payload else None),
    )

    return {
        "message": ("Job dismissed"),
        "state": (serialize_model(record)),
    }


@app.post("/jobs/{job_id}/apply")
def apply_to_job(
    job_id: int,
    payload: NotesRequest | None = None,
    profile_name: str = DEFAULT_PROFILE,
    session: Session = Depends(get_db),
):
    record = set_job_state(
        session,
        job_id=job_id,
        profile_name=(profile_name),
        status="applied",
        notes=(payload.notes if payload else None),
    )

    return {
        "message": ("Job marked as applied"),
        "state": (serialize_model(record)),
    }


@app.post("/jobs/{job_id}/seen")
def mark_job_seen(
    job_id: int,
    profile_name: str = DEFAULT_PROFILE,
    session: Session = Depends(get_db),
):
    record = set_job_state(
        session,
        job_id=job_id,
        profile_name=(profile_name),
        status="seen",
    )

    return {
        "message": ("Job marked as seen"),
        "state": (serialize_model(record)),
    }


@app.post("/jobs/{job_id}/interviewing")
def mark_interviewing(
    job_id: int,
    payload: NotesRequest | None = None,
    profile_name: str = DEFAULT_PROFILE,
    session: Session = Depends(get_db),
):
    record = set_job_state(
        session,
        job_id=job_id,
        profile_name=(profile_name),
        status="interviewing",
        notes=(payload.notes if payload else None),
    )

    return {
        "message": ("Job marked as interviewing"),
        "state": (serialize_model(record)),
    }


@app.post("/jobs/{job_id}/rejected")
def mark_rejected(
    job_id: int,
    payload: NotesRequest | None = None,
    profile_name: str = DEFAULT_PROFILE,
    session: Session = Depends(get_db),
):
    record = set_job_state(
        session,
        job_id=job_id,
        profile_name=(profile_name),
        status="rejected",
        notes=(payload.notes if payload else None),
    )

    return {
        "message": ("Job marked as rejected"),
        "state": (serialize_model(record)),
    }


@app.post("/jobs/{job_id}/offer")
def mark_offer(
    job_id: int,
    payload: NotesRequest | None = None,
    profile_name: str = DEFAULT_PROFILE,
    session: Session = Depends(get_db),
):
    record = set_job_state(
        session,
        job_id=job_id,
        profile_name=(profile_name),
        status="offer",
        notes=(payload.notes if payload else None),
    )

    return {
        "message": ("Job marked as offer"),
        "state": (serialize_model(record)),
    }


@app.get("/saved-jobs")
def get_saved_jobs(
    profile_name: str = DEFAULT_PROFILE,
    limit: int = Query(
        100,
        ge=1,
        le=500,
    ),
    session: Session = Depends(get_db),
):
    rows = session.execute(
        select(
            JobApplicationStateRecord,
            JobRecord,
        )
        .join(
            JobRecord,
            JobRecord.id == JobApplicationStateRecord.job_id,
        )
        .where(JobApplicationStateRecord.profile_name == profile_name)
        .where(JobApplicationStateRecord.status == "saved")
        .order_by(JobApplicationStateRecord.updated_at.desc())
        .limit(limit)
    ).all()

    return {
        "profile_name": (profile_name),
        "count": (len(rows)),
        "jobs": [
            {
                "job": (compact_job(job)),
                "state": (serialize_model(state)),
            }
            for (
                state,
                job,
            ) in rows
        ],
    }


@app.get("/applications")
def get_applications(
    profile_name: str = DEFAULT_PROFILE,
    status: str | None = None,
    limit: int = Query(
        100,
        ge=1,
        le=500,
    ),
    session: Session = Depends(get_db),
):
    application_statuses = {
        "applied",
        "interviewing",
        "rejected",
        "offer",
    }

    stmt = (
        select(
            JobApplicationStateRecord,
            JobRecord,
        )
        .join(
            JobRecord,
            JobRecord.id == JobApplicationStateRecord.job_id,
        )
        .where(JobApplicationStateRecord.profile_name == profile_name)
    )

    if status:
        normalized_status = status.strip().lower()

        if normalized_status not in application_statuses:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": ("Invalid application status"),
                    "allowed_statuses": (sorted(application_statuses)),
                },
            )

        stmt = stmt.where(JobApplicationStateRecord.status == normalized_status)

    else:
        stmt = stmt.where(JobApplicationStateRecord.status.in_(application_statuses))

    stmt = stmt.order_by(JobApplicationStateRecord.updated_at.desc()).limit(limit)

    rows = session.execute(stmt).all()

    return {
        "profile_name": (profile_name),
        "status": (status),
        "count": (len(rows)),
        "applications": [
            {
                "job": (compact_job(job)),
                "state": (serialize_model(state)),
            }
            for (
                state,
                job,
            ) in rows
        ],
    }


@app.get("/application-state-summary")
def application_state_summary(
    profile_name: str = DEFAULT_PROFILE,
    session: Session = Depends(get_db),
):
    rows = session.execute(
        select(
            JobApplicationStateRecord.status,
            func.count(JobApplicationStateRecord.id),
        )
        .where(JobApplicationStateRecord.profile_name == profile_name)
        .group_by(JobApplicationStateRecord.status)
        .order_by(JobApplicationStateRecord.status)
    ).all()

    counts = {
        status: int(count)
        for (
            status,
            count,
        ) in rows
    }

    for status in VALID_JOB_STATUSES:
        counts.setdefault(
            status,
            0,
        )

    return {
        "profile_name": (profile_name),
        "counts": (counts),
    }


@app.get("/pipeline-runs")
def get_pipeline_runs(
    limit: int = Query(
        20,
        ge=1,
        le=200,
    ),
    session: Session = Depends(get_db),
):
    rows = session.scalars(
        select(PipelineRunRecord).order_by(PipelineRunRecord.id.desc()).limit(limit)
    ).all()

    return {
        "count": (len(rows)),
        "pipeline_runs": [serialize_model(row) for row in rows],
    }


@app.get("/pipeline-runs/{run_id}")
def get_pipeline_run(
    run_id: int,
    session: Session = Depends(get_db),
):
    record = session.get(
        PipelineRunRecord,
        run_id,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=("Pipeline run not found"),
        )

    ranking_count = session.scalar(
        select(func.count())
        .select_from(JobRankingRecord)
        .where(JobRankingRecord.pipeline_run_id == run_id)
    )

    bucket_rows = session.execute(
        select(
            JobRankingRecord.bucket,
            func.count(JobRankingRecord.id),
        )
        .where(JobRankingRecord.pipeline_run_id == run_id)
        .group_by(JobRankingRecord.bucket)
    ).all()

    buckets = {
        bucket: int(count)
        for (
            bucket,
            count,
        ) in bucket_rows
    }

    return {
        "pipeline_run": (serialize_model(record)),
        "ranking_count": int(ranking_count or 0),
        "ranking_buckets": (buckets),
    }


@app.post("/pipeline/run")
async def trigger_pipeline():
    try:
        return await start_temporal_pipeline()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(f"Unable to start pipeline: {exc}"),
        ) from exc


@app.get("/stats")
def stats(
    session: Session = Depends(get_db),
):
    active_jobs = session.scalar(
        select(func.count()).select_from(JobRecord).where(JobRecord.is_active.is_(True))
    )

    total_jobs = session.scalar(select(func.count()).select_from(JobRecord))

    enrichments = session.scalar(select(func.count()).select_from(JobEnrichmentRecord))

    gaps = session.scalar(select(func.count()).select_from(JobGapAnalysisRecord))

    assets = session.scalar(select(func.count()).select_from(JobApplicationAssetRecord))

    rankings = session.scalar(select(func.count()).select_from(JobRankingRecord))

    pipeline_runs = session.scalar(select(func.count()).select_from(PipelineRunRecord))

    states = session.scalar(select(func.count()).select_from(JobApplicationStateRecord))

    return {
        "jobs": {
            "total": int(total_jobs or 0),
            "active": int(active_jobs or 0),
        },
        "enrichments": int(enrichments or 0),
        "gap_analyses": int(gaps or 0),
        "application_assets": int(assets or 0),
        "application_states": int(states or 0),
        "ranking_records": int(rankings or 0),
        "pipeline_runs": int(pipeline_runs or 0),
    }
