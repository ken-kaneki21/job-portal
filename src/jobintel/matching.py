import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobintel.db.models import JobRecord
from jobintel.dedup import canonical_key
from jobintel.models.job import Job

MIN_DESCRIPTION_SIMILARITY = 0.85
MIN_MULTI_CANDIDATE_SIMILARITY = 0.92
MIN_WINNER_MARGIN = 0.05


@dataclass(frozen=True)
class MatchResult:
    matched: bool
    job_id: int | None
    confidence: float
    reason: str


def tokenize(
    value: str | None,
) -> set[str]:
    if not value:
        return set()

    value = value.lower()

    tokens = re.findall(
        r"[a-z0-9+#]+",
        value,
    )

    return {token for token in tokens if len(token) > 1}


def description_similarity(
    left: str | None,
    right: str | None,
) -> float:
    left_tokens = tokenize(left)
    right_tokens = tokenize(right)

    if not left_tokens or not right_tokens:
        return 0.0

    intersection = len(left_tokens & right_tokens)

    union = len(left_tokens | right_tokens)

    if union == 0:
        return 0.0

    return intersection / union


def find_cross_source_match(
    session: Session,
    job: Job,
) -> MatchResult:
    key = canonical_key(
        company=job.company,
        title=job.title,
        location=job.location,
    )

    candidates = session.scalars(
        select(JobRecord).where(
            JobRecord.canonical_key == key,
            JobRecord.is_active.is_(True),
        )
    ).all()

    if not candidates:
        return MatchResult(
            matched=False,
            job_id=None,
            confidence=0.0,
            reason="no_candidate",
        )

    scored = [
        (
            candidate,
            description_similarity(
                job.description,
                candidate.description,
            ),
        )
        for candidate in candidates
    ]

    scored.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    best_job, best_score = scored[0]

    if len(scored) == 1:
        if best_score >= MIN_DESCRIPTION_SIMILARITY:
            return MatchResult(
                matched=True,
                job_id=best_job.id,
                confidence=best_score,
                reason=("canonical_key_and_description"),
            )

        return MatchResult(
            matched=False,
            job_id=None,
            confidence=best_score,
            reason="single_candidate_low_similarity",
        )

    second_score = scored[1][1]

    winner_margin = best_score - second_score

    if (
        best_score >= MIN_MULTI_CANDIDATE_SIMILARITY
        and winner_margin >= MIN_WINNER_MARGIN
    ):
        return MatchResult(
            matched=True,
            job_id=best_job.id,
            confidence=best_score,
            reason=("high_confidence_multi_candidate"),
        )

    return MatchResult(
        matched=False,
        job_id=None,
        confidence=best_score,
        reason="ambiguous_candidates",
    )
