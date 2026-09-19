from datetime import UTC

from sqlalchemy import select

from jobintel.db.models import PipelineRunRecord
from jobintel.db.session import SessionLocal

DEFAULT_LIMIT = 10


def format_duration(
    started_at,
    finished_at,
) -> str:
    if started_at is None or finished_at is None:
        return "-"

    duration = finished_at - started_at

    seconds = int(duration.total_seconds())

    return f"{seconds}s"


def format_datetime(
    value,
) -> str:
    if value is None:
        return "-"

    value = value.astimezone(UTC)

    return value.strftime("%Y-%m-%d %H:%M:%S UTC")


def main() -> None:
    with SessionLocal() as session:
        runs = session.scalars(
            select(PipelineRunRecord)
            .order_by(PipelineRunRecord.id.desc())
            .limit(DEFAULT_LIMIT)
        ).all()

    print()
    print("=" * 110)
    print("PIPELINE RUN HISTORY")
    print("=" * 110)

    if not runs:
        print()
        print("No pipeline runs found.")
        return

    for run in runs:
        status = "SUCCESS" if run.success else "FAILED"

        print()
        print(f"Run ID: {run.id}")

        print(f"Status: {status}")

        print(f"Started: {format_datetime(run.started_at)}")

        print(f"Finished: {format_datetime(run.finished_at)}")

        print(f"Duration: {format_duration(run.started_at, run.finished_at)}")

        print(f"Jobs fetched: {run.jobs_fetched}")

        print(f"Active jobs: {run.active_jobs}")

        print(f"Eligible jobs: {run.eligible_jobs}")

        print(f"Rankings persisted: {run.rankings_persisted}")

        if run.error_message:
            print(f"Error: {run.error_message}")

        print("-" * 110)


if __name__ == "__main__":
    main()
