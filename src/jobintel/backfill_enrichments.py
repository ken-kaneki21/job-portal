import hashlib

from sqlalchemy import select

from jobintel.db.models import (
    JobEnrichmentRecord,
    JobRecord,
)
from jobintel.db.session import (
    SessionLocal,
)
from jobintel.enrichment.extractor import (
    EXTRACTOR_VERSION,
    extract_job_enrichment,
)


BATCH_SIZE = 100


def build_content_hash(
    *,
    title: str,
    description: str | None,
) -> str:
    raw = (
        f"{title}\n"
        f"{description or ''}"
    )

    return hashlib.sha256(
        raw.encode(
            "utf-8"
        )
    ).hexdigest()


def main() -> None:
    inserted = 0
    updated = 0
    skipped = 0
    failed = 0

    with SessionLocal() as session:
        jobs = session.scalars(
            select(
                JobRecord
            )
            .where(
                JobRecord.is_active.is_(
                    True
                )
            )
            .order_by(
                JobRecord.id
            )
        ).all()

        job_ids = [
            job.id
            for job in jobs
        ]

        existing_map: dict[
            int,
            JobEnrichmentRecord,
        ] = {}

        if job_ids:
            existing_rows = (
                session.scalars(
                    select(
                        JobEnrichmentRecord
                    )
                    .where(
                        JobEnrichmentRecord.job_id.in_(
                            job_ids
                        )
                    )
                ).all()
            )

            existing_map = {
                row.job_id: row
                for row in existing_rows
            }

        print()
        print("=" * 100)
        print(
            "JOB ENRICHMENT BACKFILL"
        )
        print("=" * 100)

        print(
            f"Active jobs: "
            f"{len(jobs)}"
        )

        for (
            index,
            job,
        ) in enumerate(
            jobs,
            start=1,
        ):
            try:
                content_hash = (
                    build_content_hash(
                        title=job.title,
                        description=(
                            job.description
                        ),
                    )
                )

                existing = (
                    existing_map.get(
                        job.id
                    )
                )

                if (
                    existing is not None
                    and existing.content_hash
                    == content_hash
                    and existing.extractor_version
                    == EXTRACTOR_VERSION
                ):
                    skipped += 1
                    continue

                enrichment = (
                    extract_job_enrichment(
                        title=job.title,
                        description=(
                            job.description
                        ),
                    )
                )

                payload = (
                    enrichment.to_dict()
                )

                if existing is None:
                    record = (
                        JobEnrichmentRecord(
                            job_id=job.id,
                            extractor_version=(
                                EXTRACTOR_VERSION
                            ),
                            content_hash=(
                                content_hash
                            ),
                            minimum_experience_years=(
                                enrichment
                                .minimum_experience_years
                            ),
                            maximum_experience_years=(
                                enrichment
                                .maximum_experience_years
                            ),
                            seniority=(
                                enrichment
                                .seniority
                            ),
                            employment_type=(
                                enrichment
                                .employment_type
                            ),
                            education=(
                                enrichment
                                .education
                            ),
                            required_skills=(
                                enrichment
                                .required_skills
                            ),
                            preferred_skills=(
                                enrichment
                                .preferred_skills
                            ),
                            cloud_platforms=(
                                enrichment
                                .cloud_platforms
                            ),
                            data_platforms=(
                                enrichment
                                .data_platforms
                            ),
                            responsibilities=(
                                enrichment
                                .responsibilities
                            ),
                            deal_breakers=(
                                enrichment
                                .deal_breakers
                            ),
                            extracted_payload=(
                                payload
                            ),
                        )
                    )

                    session.add(
                        record
                    )

                    existing_map[
                        job.id
                    ] = record

                    inserted += 1

                else:
                    existing.extractor_version = (
                        EXTRACTOR_VERSION
                    )

                    existing.content_hash = (
                        content_hash
                    )

                    existing.minimum_experience_years = (
                        enrichment
                        .minimum_experience_years
                    )

                    existing.maximum_experience_years = (
                        enrichment
                        .maximum_experience_years
                    )

                    existing.seniority = (
                        enrichment.seniority
                    )

                    existing.employment_type = (
                        enrichment
                        .employment_type
                    )

                    existing.education = (
                        enrichment.education
                    )

                    existing.required_skills = (
                        enrichment
                        .required_skills
                    )

                    existing.preferred_skills = (
                        enrichment
                        .preferred_skills
                    )

                    existing.cloud_platforms = (
                        enrichment
                        .cloud_platforms
                    )

                    existing.data_platforms = (
                        enrichment
                        .data_platforms
                    )

                    existing.responsibilities = (
                        enrichment
                        .responsibilities
                    )

                    existing.deal_breakers = (
                        enrichment
                        .deal_breakers
                    )

                    existing.extracted_payload = (
                        payload
                    )

                    updated += 1

                if (
                    index
                    % BATCH_SIZE
                    == 0
                ):
                    session.commit()

                    print(
                        f"Processed "
                        f"{index}/"
                        f"{len(jobs)}"
                    )

            except Exception as exc:
                session.rollback()

                failed += 1

                print(
                    f"FAILED job "
                    f"{job.id}: "
                    f"{exc}"
                )

        session.commit()

    print()
    print("=" * 100)
    print(
        "ENRICHMENT BACKFILL SUMMARY"
    )
    print("=" * 100)

    print(
        f"Inserted: "
        f"{inserted}"
    )

    print(
        f"Updated:  "
        f"{updated}"
    )

    print(
        f"Skipped:  "
        f"{skipped}"
    )

    print(
        f"Failed:   "
        f"{failed}"
    )


if __name__ == "__main__":
    main()