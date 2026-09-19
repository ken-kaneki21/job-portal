from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from jobintel.db.models import (
    JobRecord,
    JobSourceRecord,
)
from jobintel.db.session import SessionLocal


def main() -> None:
    with SessionLocal() as session:
        jobs = session.scalars(
            select(JobRecord)
        ).all()

        if not jobs:
            print("No jobs found.")
            return

        values = [
            {
                "job_id": job.id,
                "source": job.source,
                "source_identifier": job.source_identifier,
                "external_id": job.external_id,
                "source_url": job.apply_url,
                "is_primary": True,
            }
            for job in jobs
        ]

        statement = insert(
            JobSourceRecord
        ).values(values)

        statement = statement.on_conflict_do_nothing(
            constraint="uq_job_source_identity"
        )

        session.execute(statement)
        session.commit()

    print(
        f"Source references backfilled: "
        f"{len(values)}"
    )


if __name__ == "__main__":
    main()