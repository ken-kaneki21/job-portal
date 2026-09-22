import hashlib
import json

from sqlalchemy import select

from jobintel.db.models import (
    JobEnrichmentRecord,
    JobGapAnalysisRecord,
    JobRecord,
)
from jobintel.db.session import (
    SessionLocal,
)
from jobintel.gap_analysis.analyzer import (
    ANALYZER_VERSION,
    analyze_job_gap,
)
from jobintel.profile.loader import (
    load_profile,
)
from jobintel.profile.runtime import ACTIVE_PROFILE_PATH

PROFILE_PATH = ACTIVE_PROFILE_PATH

BATCH_SIZE = 100


def build_content_hash(
    *,
    profile,
    enrichment: JobEnrichmentRecord,
) -> str:
    profile_payload = {
        "name": getattr(
            profile,
            "name",
            None,
        ),
        "core_skills": sorted(
            getattr(
                profile,
                "core_skills",
                [],
            )
        ),
        "secondary_skills": sorted(
            getattr(
                profile,
                "secondary_skills",
                [],
            )
        ),
        "experience_years": getattr(
            profile,
            "experience_years",
            None,
        ),
        "years_of_experience": getattr(
            profile,
            "years_of_experience",
            None,
        ),
    }

    payload = {
        "analyzer_version": (ANALYZER_VERSION),
        "enrichment_hash": (enrichment.content_hash),
        # Important:
        # extractor behavior can change even when
        # title/description text stays identical.
        "enrichment_extractor_version": (
            getattr(
                enrichment,
                "extractor_version",
                None,
            )
        ),
        "profile": (profile_payload),
    }

    raw = json.dumps(
        payload,
        sort_keys=True,
        default=str,
    )

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main() -> None:
    profile = load_profile(PROFILE_PATH)

    inserted = 0
    updated = 0
    skipped = 0
    failed = 0

    with SessionLocal() as session:
        rows = session.execute(
            select(
                JobRecord,
                JobEnrichmentRecord,
            )
            .join(
                JobEnrichmentRecord,
                JobEnrichmentRecord.job_id == JobRecord.id,
            )
            .where(JobRecord.is_active.is_(True))
            .order_by(JobRecord.id)
        ).all()

        job_ids = [
            job.id
            for (
                job,
                enrichment,
            ) in rows
        ]

        existing_map: dict[
            int,
            JobGapAnalysisRecord,
        ] = {}

        if job_ids:
            existing_rows = session.scalars(
                select(JobGapAnalysisRecord)
                .where(JobGapAnalysisRecord.profile_name == profile.name)
                .where(JobGapAnalysisRecord.job_id.in_(job_ids))
            ).all()

            existing_map = {row.job_id: row for row in existing_rows}

        print()
        print("=" * 100)
        print("JOB GAP ANALYSIS BACKFILL")
        print("=" * 100)

        print(f"Profile: {profile.name}")

        print(f"Enriched active jobs: {len(rows)}")

        for index, (
            job,
            enrichment,
        ) in enumerate(
            rows,
            start=1,
        ):
            try:
                content_hash = build_content_hash(
                    profile=profile,
                    enrichment=(enrichment),
                )

                existing = existing_map.get(job.id)

                if (
                    existing is not None
                    and existing.content_hash == content_hash
                    and existing.analyzer_version == ANALYZER_VERSION
                ):
                    skipped += 1
                    continue

                analysis = analyze_job_gap(
                    profile=profile,
                    enrichment=(enrichment),
                )

                payload = analysis.to_dict()

                if existing is None:
                    record = JobGapAnalysisRecord(
                        job_id=job.id,
                        profile_name=(profile.name),
                        analyzer_version=(ANALYZER_VERSION),
                        content_hash=(content_hash),
                        matched_required_skills=(analysis.matched_required_skills),
                        missing_required_skills=(analysis.missing_required_skills),
                        matched_preferred_skills=(analysis.matched_preferred_skills),
                        missing_preferred_skills=(analysis.missing_preferred_skills),
                        matched_platforms=(analysis.matched_platforms),
                        missing_platforms=(analysis.missing_platforms),
                        deal_breakers=(analysis.deal_breakers),
                        experience_fit=(analysis.experience_fit),
                        experience_gap_years=(analysis.experience_gap_years),
                        required_skill_match_ratio=(
                            analysis.required_skill_match_ratio
                        ),
                        preferred_skill_match_ratio=(
                            analysis.preferred_skill_match_ratio
                        ),
                        platform_match_ratio=(analysis.platform_match_ratio),
                        gap_score=(analysis.gap_score),
                        fit_summary=(analysis.fit_summary),
                        analysis_payload=(payload),
                    )

                    session.add(record)

                    existing_map[job.id] = record

                    inserted += 1

                else:
                    existing.analyzer_version = ANALYZER_VERSION

                    existing.content_hash = content_hash

                    existing.matched_required_skills = analysis.matched_required_skills

                    existing.missing_required_skills = analysis.missing_required_skills

                    existing.matched_preferred_skills = (
                        analysis.matched_preferred_skills
                    )

                    existing.missing_preferred_skills = (
                        analysis.missing_preferred_skills
                    )

                    existing.matched_platforms = analysis.matched_platforms

                    existing.missing_platforms = analysis.missing_platforms

                    existing.deal_breakers = analysis.deal_breakers

                    existing.experience_fit = analysis.experience_fit

                    existing.experience_gap_years = analysis.experience_gap_years

                    existing.required_skill_match_ratio = (
                        analysis.required_skill_match_ratio
                    )

                    existing.preferred_skill_match_ratio = (
                        analysis.preferred_skill_match_ratio
                    )

                    existing.platform_match_ratio = analysis.platform_match_ratio

                    existing.gap_score = analysis.gap_score

                    existing.fit_summary = analysis.fit_summary

                    existing.analysis_payload = payload

                    updated += 1

                if index % BATCH_SIZE == 0:
                    session.commit()

                    print(f"Processed {index}/{len(rows)}")

            except Exception as exc:
                session.rollback()

                failed += 1

                print(f"FAILED job {job.id}: {exc}")

        session.commit()

    print()
    print("=" * 100)
    print("GAP ANALYSIS SUMMARY")
    print("=" * 100)

    print(f"Inserted: {inserted}")

    print(f"Updated:  {updated}")

    print(f"Skipped:  {skipped}")

    print(f"Failed:   {failed}")


if __name__ == "__main__":
    main()
