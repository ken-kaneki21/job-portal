from sqlalchemy.dialects.postgresql import insert

from jobintel.db.models import CompanyRecord
from jobintel.db.session import SessionLocal

COMPANIES = [
    {
        "name": "Take-Two Interactive",
        "ats": "greenhouse",
        "identifier": "taketwo",
        "priority": 50,
    },
    {
        "name": "Datadog",
        "ats": "greenhouse",
        "identifier": "datadog",
        "priority": 100,
    },
    {
        "name": "Cloudflare",
        "ats": "greenhouse",
        "identifier": "cloudflare",
        "priority": 100,
    },
    {
        "name": "Fam",
        "ats": "lever",
        "identifier": "fampay",
        "priority": 25,
    },
    {
        "name": "Ashby",
        "ats": "ashby",
        "identifier": "Ashby",
        "priority": 100,
    },
    {
        "name": "SmartRecruiters",
        "ats": "smartrecruiters",
        "identifier": "smartrecruiters",
        "priority": 100,
    },
]


def main() -> None:
    with SessionLocal() as session:
        statement = insert(CompanyRecord).values(COMPANIES)

        statement = statement.on_conflict_do_nothing(
            constraint="uq_company_ats_identifier"
        )

        session.execute(statement)
        session.commit()

    print("Company registry seeded.")


if __name__ == "__main__":
    main()
