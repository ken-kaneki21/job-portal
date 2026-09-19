from sqlalchemy import select

from jobintel.db.models import CompanyRecord
from jobintel.db.session import SessionLocal
from jobintel.models.company import Company


def load_companies() -> list[Company]:
    with SessionLocal() as session:
        records = session.scalars(
            select(CompanyRecord)
            .where(CompanyRecord.enabled.is_(True))
            .order_by(
                CompanyRecord.priority,
                CompanyRecord.name,
            )
        ).all()

    return [
        Company(
            name=record.name,
            ats=record.ats,
            identifier=record.identifier,
            enabled=record.enabled,
        )
        for record in records
    ]
