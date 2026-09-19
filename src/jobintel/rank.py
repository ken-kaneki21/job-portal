import os
from collections import defaultdict
from dataclasses import replace

from sqlalchemy import select

from jobintel.db.models import (
    JobGapAnalysisRecord,
    JobRecord,
    JobSourceRecord,
)
from jobintel.db.ranking_repository import (
    save_rankings,
)
from jobintel.db.session import (
    SessionLocal,
)
from jobintel.profile.loader import (
    load_profile,
)
from jobintel.ranking.scoring import (
    rank_job,
)
from jobintel.semantic.embeddings import (
    embed_text,
)
from jobintel.semantic.profile_text import (
    build_profile_text,
)
from jobintel.semantic.scoring import (
    load_job_embedding,
    score_semantic_similarity,
)


PROFILE_PATH = (
    "profiles/data_engineer.json"
)

MIN_SCORE = 40.0

HIGH_CONFIDENCE_LIMIT = 15
DISCOVERY_LIMIT = 15
STRETCH_LIMIT = 15


# ---------------------------------------------------------
# Final ranking weights
# ---------------------------------------------------------

DETERMINISTIC_WEIGHT = 0.75
GAP_WEIGHT = 0.15

# semantic_score is already on a 0..10 scale.
# Therefore it contributes a maximum of 10 points directly.
DEFAULT_GAP_SCORE = 50.0


def is_direct_source(
    result,
) -> bool:
    direct_sources = {
        "greenhouse",
        "lever",
        "ashby",
        "smartrecruiters",
    }

    return any(
        source in direct_sources
        for source in result.sources
    )


def is_aggregator_only(
    result,
) -> bool:
    if not result.sources:
        return False

    return (
        set(
            result.sources
        )
        == {
            "adzuna"
        }
    )


def classify_result(
    result,
) -> str:
    """
    Returns one of:

    - high_confidence
    - discovery
    - stretch
    """

    experience = (
        result.detected_experience
    )

    # Known 5+ year requirements remain
    # stretch opportunities.
    if (
        experience is not None
        and experience >= 5
    ):
        return "stretch"

    # Direct employer ATS posting with
    # strong score and acceptable experience.
    if (
        is_direct_source(
            result
        )
        and result.score >= 65
        and result.experience_score
        >= 10
    ):
        return "high_confidence"

    # Aggregator-only jobs remain discovery.
    if is_aggregator_only(
        result
    ):
        return "discovery"

    return "discovery"


def print_job(
    index: int,
    result,
) -> None:
    job = result.job

    gap_score = getattr(
        result,
        "gap_score",
        DEFAULT_GAP_SCORE,
    )

    semantic_score = getattr(
        result,
        "semantic_score",
        0.0,
    )

    deterministic_score = getattr(
        result,
        "deterministic_score",
        None,
    )

    print()

    print(
        f"#{index}  "
        f"{job.title}"
    )

    print(
        f"{job.company} | "
        f"{job.location or 'Unknown'}"
    )

    print(
        f"SCORE: "
        f"{result.score:.1f}/100"
    )

    print(
        "Breakdown: "
        f"title="
        f"{result.title_score:.0f} "
        f"location="
        f"{result.location_score:.0f} "
        f"skills="
        f"{result.skill_score:.1f} "
        f"experience="
        f"{result.experience_score:.0f} "
        f"freshness="
        f"{result.freshness_score:.0f} "
        f"source="
        f"{result.source_score:.0f} "
        f"semantic="
        f"{semantic_score:.1f} "
        f"gap="
        f"{gap_score:.1f}"
    )

    if deterministic_score is not None:
        print(
            "Score components: "
            f"deterministic="
            f"{deterministic_score:.1f} "
            f"semantic="
            f"{semantic_score:.1f} "
            f"gap="
            f"{gap_score:.1f}"
        )

    if result.sources:
        print(
            "Sources: "
            + ", ".join(
                result.sources
            )
        )

    if result.reasons:
        print(
            "Why: "
            + " | ".join(
                result.reasons
            )
        )

    print(
        "Apply: "
        f"{result.preferred_apply_url}"
    )

    print(
        "-" * 100
    )


def print_section(
    title: str,
    results: list,
    limit: int,
) -> None:
    print()

    print(
        "=" * 100
    )

    print(
        title
    )

    print(
        "=" * 100
    )

    if not results:
        print()

        print(
            "No jobs in this category."
        )

        return

    for index, result in enumerate(
        results[:limit],
        start=1,
    ):
        print_job(
            index,
            result,
        )


def main() -> None:
    # -----------------------------------------------------
    # Load candidate profile
    # -----------------------------------------------------

    profile = load_profile(
        PROFILE_PATH
    )

    # -----------------------------------------------------
    # Build profile embedding once
    # -----------------------------------------------------

    profile_text = (
        build_profile_text(
            profile
        )
    )

    profile_embedding = (
        embed_text(
            profile_text
        )
    )

    # -----------------------------------------------------
    # Load active jobs, provenance and gap analysis
    # -----------------------------------------------------

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
        ).all()

        job_ids = [
            job.id
            for job in jobs
        ]

        # -------------------------------------------------
        # Source provenance
        # -------------------------------------------------

        source_map: dict[
            int,
            list[
                JobSourceRecord
            ],
        ] = defaultdict(
            list
        )

        if job_ids:
            source_rows = (
                session.scalars(
                    select(
                        JobSourceRecord
                    )
                    .where(
                        JobSourceRecord
                        .job_id
                        .in_(
                            job_ids
                        )
                    )
                )
                .all()
            )

            for source in source_rows:
                source_map[
                    source.job_id
                ].append(
                    source
                )

        # -------------------------------------------------
        # Structured gap analysis
        # -------------------------------------------------

        gap_map: dict[
            int,
            JobGapAnalysisRecord,
        ] = {}

        if job_ids:
            gap_rows = (
                session.scalars(
                    select(
                        JobGapAnalysisRecord
                    )
                    .where(
                        JobGapAnalysisRecord
                        .job_id
                        .in_(
                            job_ids
                        )
                    )
                    .where(
                        JobGapAnalysisRecord
                        .profile_name
                        == profile.name
                    )
                )
                .all()
            )

            gap_map = {
                row.job_id: row
                for row in gap_rows
            }

        # -------------------------------------------------
        # Deterministic + semantic + gap ranking
        # -------------------------------------------------

        evaluated = []

        for job in jobs:
            result = rank_job(
                job,
                profile,
                source_map.get(
                    job.id,
                    [],
                ),
            )

            # ---------------------------------------------
            # Hard-filtered jobs remain rejected.
            # Do not waste embedding work on them.
            # ---------------------------------------------

            if not result.eligible:
                evaluated.append(
                    result
                )

                continue

            # ---------------------------------------------
            # Semantic similarity
            # ---------------------------------------------

            job_embedding = (
                load_job_embedding(
                    session,
                    job.id,
                )
            )

            semantic_score = (
                score_semantic_similarity(
                    profile_embedding=(
                        profile_embedding
                    ),
                    job_embedding=(
                        job_embedding
                    ),
                )
            )

            # ---------------------------------------------
            # Structured gap score
            # ---------------------------------------------

            gap_record = (
                gap_map.get(
                    job.id
                )
            )

            if gap_record is None:
                gap_score = (
                    DEFAULT_GAP_SCORE
                )

            else:
                gap_score = float(
                    gap_record.gap_score
                )

            # ---------------------------------------------
            # Final blended score
            #
            # deterministic:
            #   0..100 * .75 = 0..75
            #
            # semantic:
            #   already 0..10 = 0..10
            #
            # gap:
            #   0..100 * .15 = 0..15
            #
            # total:
            #   0..100
            # ---------------------------------------------

            deterministic_score = float(
                result.score
            )

            final_score = round(
                (
                    deterministic_score
                    * DETERMINISTIC_WEIGHT
                )
                + float(
                    semantic_score
                )
                + (
                    gap_score
                    * GAP_WEIGHT
                ),
                2,
            )

            # Clamp to expected range.
            final_score = min(
                100.0,
                max(
                    0.0,
                    final_score,
                ),
            )

            # ---------------------------------------------
            # RankedJob is frozen.
            # Create a replacement object.
            # ---------------------------------------------

            result = replace(
                result,
                score=final_score,
                deterministic_score=(
                    deterministic_score
                ),
                semantic_score=(
                    float(
                        semantic_score
                    )
                ),
                gap_score=(
                    gap_score
                ),
            )

            evaluated.append(
                result
            )

    # -----------------------------------------------------
    # Filter
    # -----------------------------------------------------

    rejected = [
        result
        for result in evaluated
        if not result.eligible
    ]

    eligible = [
        result
        for result in evaluated
        if (
            result.eligible
            and result.score
            >= MIN_SCORE
        )
    ]

    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    eligible.sort(
        key=lambda item: (
            item.score,
            item.source_score,
            getattr(
                item,
                "gap_score",
                DEFAULT_GAP_SCORE,
            ),
        ),
        reverse=True,
    )

    # -----------------------------------------------------
    # Buckets
    # -----------------------------------------------------

    high_confidence = []
    discovery = []
    stretch = []

    for result in eligible:
        bucket = (
            classify_result(
                result
            )
        )

        if (
            bucket
            == "high_confidence"
        ):
            high_confidence.append(
                result
            )

        elif (
            bucket
            == "stretch"
        ):
            stretch.append(
                result
            )

        else:
            discovery.append(
                result
            )

    # -----------------------------------------------------
    # Pipeline run context
    # -----------------------------------------------------

    pipeline_run_id_value = (
        os.getenv(
            "JOBINTEL_PIPELINE_RUN_ID"
        )
    )

    pipeline_run_id = (
        int(
            pipeline_run_id_value
        )
        if pipeline_run_id_value
        else None
    )

    # -----------------------------------------------------
    # Persist ranking snapshot
    # -----------------------------------------------------

    with SessionLocal() as session:
        saved = save_rankings(
            session=session,
            profile_name=(
                profile.name
            ),
            high_confidence=(
                high_confidence
            ),
            discovery=(
                discovery
            ),
            stretch=(
                stretch
            ),
            pipeline_run_id=(
                pipeline_run_id
            ),
        )

        session.commit()

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print()

    print(
        f"Profile: "
        f"{profile.name}"
    )

    print(
        "Active jobs evaluated: "
        f"{len(jobs)}"
    )

    print(
        "Rejected by hard filters: "
        f"{len(rejected)}"
    )

    print(
        "Eligible above threshold: "
        f"{len(eligible)}"
    )

    print()

    print(
        "High confidence: "
        f"{len(high_confidence)}"
    )

    print(
        "Discovery:       "
        f"{len(discovery)}"
    )

    print(
        "Stretch:         "
        f"{len(stretch)}"
    )

    print(
        "Rankings persisted: "
        f"{saved}"
    )

    # -----------------------------------------------------
    # Output
    # -----------------------------------------------------

    print_section(
        "HIGH CONFIDENCE",
        high_confidence,
        HIGH_CONFIDENCE_LIMIT,
    )

    print_section(
        "DISCOVERY",
        discovery,
        DISCOVERY_LIMIT,
    )

    print_section(
        "STRETCH",
        stretch,
        STRETCH_LIMIT,
    )


if __name__ == "__main__":
    main()