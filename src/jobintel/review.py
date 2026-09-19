import argparse

from sqlalchemy import func, select

from jobintel.db.application_state_repository import (
    VALID_STATUSES,
    set_application_state,
)
from jobintel.db.models import (
    JobApplicationStateRecord,
    JobRankingRecord,
    JobRecord,
)
from jobintel.db.session import SessionLocal

PROFILE_NAME = "data_engineer"


def get_latest_ranking_run_id(
    session,
) -> int | None:
    return session.scalar(
        select(func.max(JobRankingRecord.pipeline_run_id))
        .where(JobRankingRecord.profile_name == PROFILE_NAME)
        .where(JobRankingRecord.pipeline_run_id.is_not(None))
    )


def list_jobs(
    status: str | None = None,
    limit: int = 25,
) -> None:
    with SessionLocal() as session:
        latest_run_id = get_latest_ranking_run_id(session)

        if latest_run_id is None:
            print("No ranking snapshot found.")
            return

        stmt = (
            select(
                JobRecord.id,
                JobRecord.title,
                JobRecord.company,
                JobRecord.location,
                JobRankingRecord.bucket,
                JobRankingRecord.score,
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
            .where(JobRankingRecord.pipeline_run_id == latest_run_id)
        )

        if status:
            stmt = stmt.where(JobApplicationStateRecord.status == status)

        else:
            stmt = stmt.where(
                (JobApplicationStateRecord.status.is_(None))
                | (
                    JobApplicationStateRecord.status.in_(
                        [
                            "new",
                            "reviewed",
                            "interview",
                            "offer",
                        ]
                    )
                )
            )

        stmt = stmt.order_by(
            JobRankingRecord.score.desc(),
            JobRankingRecord.rank_position.asc(),
        ).limit(limit)

        rows = session.execute(stmt).all()

        if not rows:
            print("No jobs found.")
            return

        print()
        print(f"Ranking run: {latest_run_id}")

        for row in rows:
            current_status = row.status if row.status else "new"

            print()
            print(f"Job ID: {row.id}")

            print(row.title)

            print(f"{row.company} | {row.location or 'Unknown'}")

            print(f"Bucket: {row.bucket}")

            print(f"Score: {row.score:.1f}")

            print(f"Status: {current_status}")

            print("-" * 80)


def update_status(
    job_id: int,
    status: str,
    notes: str | None = None,
) -> None:
    with SessionLocal() as session:
        job = session.get(
            JobRecord,
            job_id,
        )

        if job is None:
            print(f"Job {job_id} does not exist.")
            return

        record = set_application_state(
            session=session,
            job_id=job_id,
            profile_name=PROFILE_NAME,
            status=status,
            notes=notes,
        )

        session.commit()

        print(f"Updated job {job_id} to status '{record.status}'.")


def build_parser():
    parser = argparse.ArgumentParser(description=("Review and track ranked jobs."))

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    list_parser = subparsers.add_parser("list")

    list_parser.add_argument(
        "--status",
        choices=sorted(VALID_STATUSES),
        default=None,
    )

    list_parser.add_argument(
        "--limit",
        type=int,
        default=25,
    )

    for status in sorted(VALID_STATUSES):
        status_parser = subparsers.add_parser(status)

        status_parser.add_argument(
            "job_id",
            type=int,
        )

        status_parser.add_argument(
            "--notes",
            default=None,
        )

    return parser


def main() -> None:
    parser = build_parser()

    args = parser.parse_args()

    if args.command == "list":
        list_jobs(
            status=args.status,
            limit=args.limit,
        )
        return

    update_status(
        job_id=args.job_id,
        status=args.command,
        notes=args.notes,
    )


if __name__ == "__main__":
    main()
