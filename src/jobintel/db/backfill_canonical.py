from sqlalchemy import select

from jobintel.db.models import JobRecord
from jobintel.db.session import SessionLocal
from jobintel.dedup import canonical_key


def main() -> None:
    with SessionLocal() as session:
        jobs = session.scalars(
            select(JobRecord)
        ).all()

        updated = 0

        for job in jobs:
            job.canonical_key = canonical_key(
                company=job.company,
                title=job.title,
                location=job.location,
            )

            updated += 1

        session.commit()

    print(
        f"Canonical keys backfilled: "
        f"{updated}"
    )


if __name__ == "__main__":
    main()