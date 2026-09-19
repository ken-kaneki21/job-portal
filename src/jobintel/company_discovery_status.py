from sqlalchemy import func, select

from jobintel.db.models import (
    CompanyDiscoveryCandidateRecord,
)
from jobintel.db.session import SessionLocal


def main() -> None:
    with SessionLocal() as session:
        rows = session.execute(
            select(
                CompanyDiscoveryCandidateRecord.status,
                func.count(),
            )
            .group_by(CompanyDiscoveryCandidateRecord.status)
            .order_by(CompanyDiscoveryCandidateRecord.status)
        ).all()

        pending = session.scalars(
            select(CompanyDiscoveryCandidateRecord)
            .where(CompanyDiscoveryCandidateRecord.status == "pending")
            .order_by(CompanyDiscoveryCandidateRecord.id)
            .limit(20)
        ).all()

    print()
    print("=" * 100)
    print("COMPANY DISCOVERY STATUS")
    print("=" * 100)

    for status, count in rows:
        print(f"{status}: {count}")

    if pending:
        print()
        print("NEXT PENDING CANDIDATES")
        print("-" * 100)

        for candidate in pending:
            print(f"{candidate.id} | {candidate.company_name}")


if __name__ == "__main__":
    main()
