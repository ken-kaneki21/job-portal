from __future__ import annotations

import os

from sqlalchemy import select

from jobintel.db.models import JobEmbeddingRecord, JobRecord
from jobintel.db.session import SessionLocal
from jobintel.semantic.embeddings import MODEL_NAME, embed_texts
from jobintel.semantic.job_text import build_content_hash, build_job_text

INFERENCE_BATCH_SIZE = max(1, int(os.getenv("JOBINTEL_EMBEDDING_BATCH_SIZE", "32")))


def main() -> None:
    inserted = updated = skipped = failed = 0
    with SessionLocal() as session:
        jobs = session.scalars(
            select(JobRecord).where(JobRecord.is_active.is_(True))
        ).all()
        job_ids = [job.id for job in jobs]
        existing_rows = (
            session.scalars(
                select(JobEmbeddingRecord)
                .where(JobEmbeddingRecord.job_id.in_(job_ids))
                .where(JobEmbeddingRecord.model_name == MODEL_NAME)
            ).all()
            if job_ids
            else []
        )
        existing_map = {row.job_id: row for row in existing_rows}

        print("=" * 100)
        print("JOB EMBEDDING BACKFILL")
        print("=" * 100)
        print(f"Active jobs: {len(jobs)}")
        print(f"Inference batch size: {INFERENCE_BATCH_SIZE}")

        pending = []
        for job in jobs:
            text = build_job_text(job)
            content_hash = build_content_hash(text)
            existing = existing_map.get(job.id)
            if existing is not None and existing.content_hash == content_hash:
                skipped += 1
                continue
            pending.append((job, text, content_hash, existing))

        total = len(pending)
        print(f"Embeddings required: {total}")
        print(f"Unchanged skipped:   {skipped}")
        processed = 0

        for start in range(0, total, INFERENCE_BATCH_SIZE):
            chunk = pending[start : start + INFERENCE_BATCH_SIZE]
            try:
                vectors = embed_texts(
                    [item[1] for item in chunk],
                    batch_size=INFERENCE_BATCH_SIZE,
                )
            except Exception as exc:
                failed += len(chunk)
                print(f"FAILED embedding batch {start + 1}-{start + len(chunk)}: {exc}")
                continue

            for (job, _text, content_hash, existing), vector in zip(
                chunk, vectors, strict=True
            ):
                vector_value = vector.tolist()
                if existing is None:
                    session.add(
                        JobEmbeddingRecord(
                            job_id=job.id,
                            model_name=MODEL_NAME,
                            embedding=vector_value,
                            content_hash=content_hash,
                        )
                    )
                    inserted += 1
                else:
                    existing.embedding = vector_value
                    existing.content_hash = content_hash
                    updated += 1
            session.commit()
            processed += len(chunk)
            print(f"Processed {processed}/{total}")

    print("\n" + "=" * 100)
    print("EMBEDDING BACKFILL SUMMARY")
    print("=" * 100)
    print(f"Inserted: {inserted}")
    print(f"Updated:  {updated}")
    print(f"Skipped:  {skipped}")
    print(f"Failed:   {failed}")
    if failed:
        raise RuntimeError(f"{failed} embeddings failed.")


if __name__ == "__main__":
    main()
