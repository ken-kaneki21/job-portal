from sqlalchemy import select

from jobintel.db.models import (
    JobRecord,
)
from jobintel.db.session import SessionLocal
from jobintel.profile.loader import (
    load_profile,
)
from jobintel.profile.runtime import ACTIVE_PROFILE_PATH
from jobintel.semantic.embeddings import (
    cosine_similarity,
    embed_text,
)
from jobintel.semantic.job_text import (
    build_job_text,
)
from jobintel.semantic.profile_text import (
    build_profile_text,
)

PROFILE_PATH = ACTIVE_PROFILE_PATH


def main() -> None:
    profile = load_profile(PROFILE_PATH)

    profile_text = build_profile_text(profile)

    print()
    print("Loading embedding model...")

    profile_embedding = embed_text(profile_text)

    with SessionLocal() as session:
        jobs = session.scalars(
            select(JobRecord)
            .where(JobRecord.is_active.is_(True))
            .order_by(JobRecord.id.desc())
            .limit(20)
        ).all()

    scored = []

    for job in jobs:
        job_text = build_job_text(job)

        job_embedding = embed_text(job_text)

        similarity = cosine_similarity(
            profile_embedding,
            job_embedding,
        )

        scored.append(
            (
                similarity,
                job,
            )
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    print()
    print("=" * 100)
    print("SEMANTIC MATCH TEST")
    print("=" * 100)

    for similarity, job in scored:
        print()
        print(f"{similarity:.3f} | {job.title}")

        print(f"{job.company} | {job.location or 'Unknown'}")


if __name__ == "__main__":
    main()
