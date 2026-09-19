from sqlalchemy import func, select

from jobintel.db.models import (
    JobRankingRecord,
    JobRecord,
    ScanRecord,
)
from jobintel.db.session import SessionLocal


def main() -> None:
    failures = []

    with SessionLocal() as session:
        active_jobs = int(
            session.scalar(
                select(func.count())
                .select_from(JobRecord)
                .where(JobRecord.is_active.is_(True))
            )
            or 0
        )

        failed_scans = int(
            session.scalar(
                select(func.count())
                .select_from(ScanRecord)
                .where(ScanRecord.success.is_(False))
            )
            or 0
        )

        ranking_count = int(
            session.scalar(select(func.count()).select_from(JobRankingRecord)) or 0
        )

    if active_jobs < 100:
        failures.append("Active job count is unusually low.")

    if ranking_count == 0:
        failures.append("No ranking records found.")

    print()
    print("=" * 80)
    print("DATA QUALITY CHECKS")
    print("=" * 80)

    print(f"Active jobs: {active_jobs}")

    print(f"Historical failed scans: {failed_scans}")

    print(f"Ranking records: {ranking_count}")

    if failures:
        print()

        for failure in failures:
            print(f"FAIL: {failure}")

        raise RuntimeError("Data quality checks failed.")

    print()
    print("All data quality checks passed.")


if __name__ == "__main__":
    main()
