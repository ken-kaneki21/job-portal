import hashlib

from sqlalchemy import select

from jobintel.db.models import (
    JobEmbeddingRecord,
    JobRecord,
)
from jobintel.db.session import SessionLocal
from jobintel.semantic.embeddings import (
    MODEL_NAME,
    embed_text,
)
from jobintel.semantic.job_text import (
    build_job_text,
)


BATCH_SIZE = 100


def build_content_hash(
    text: str,
) -> str:
    return hashlib.sha256(
        text.encode(
            "utf-8"
        )
    ).hexdigest()


def load_existing_embedding(
    session,
    job_id: int,
):
    return session.scalar(
        select(
            JobEmbeddingRecord
        )
        .where(
            JobEmbeddingRecord.job_id
            == job_id
        )
        .where(
            JobEmbeddingRecord.model_name
            == MODEL_NAME
        )
    )


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

        print()
        print("=" * 100)
        print("JOB EMBEDDING BACKFILL")
        print("=" * 100)

        print(
            f"Active jobs: {len(jobs)}"
        )

        for index, job in enumerate(
            jobs,
            start=1,
        ):
            try:
                text = build_job_text(
                    job
                )

                content_hash = (
                    build_content_hash(
                        text
                    )
                )

                existing = (
                    load_existing_embedding(
                        session,
                        job.id,
                    )
                )

                if (
                    existing is not None
                    and existing.content_hash
                    == content_hash
                ):
                    skipped += 1
                    continue

                embedding = embed_text(
                    text
                )

                vector_value = (
                    embedding.tolist()
                )

                if existing is None:
                    record = (
                        JobEmbeddingRecord(
                            job_id=job.id,
                            model_name=MODEL_NAME,
                            embedding=vector_value,
                            content_hash=(
                                content_hash
                            ),
                        )
                    )

                    session.add(
                        record
                    )

                    inserted += 1

                else:
                    existing.embedding = (
                        vector_value
                    )

                    existing.content_hash = (
                        content_hash
                    )

                    updated += 1

                if (
                    index % BATCH_SIZE
                    == 0
                ):
                    session.commit()

                    print(
                        f"Processed {index}/"
                        f"{len(jobs)}"
                    )

            except Exception as exc:
                failed += 1

                print()
                print(
                    f"Embedding failed for "
                    f"job {job.id}: {exc}"
                )

        session.commit()

    print()
    print("=" * 100)
    print("EMBEDDING BACKFILL SUMMARY")
    print("=" * 100)

    print(
        f"Inserted: {inserted}"
    )

    print(
        f"Updated:  {updated}"
    )

    print(
        f"Skipped:  {skipped}"
    )

    print(
        f"Failed:   {failed}"
    )


if __name__ == "__main__":
    main()