from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select

from jobintel.db.application_event_model import (
    JobApplicationEventRecord,
)
from jobintel.db.models import (
    JobRankingRecord,
    JobRecord,
)
from jobintel.outcome_learning.features import (
    OutcomeFeatures,
    extract_outcome_features,
)
from jobintel.outcome_learning.history import (
    derive_historical_outcome,
)
from jobintel.profile.models import CandidateProfile

MIN_TOTAL_OUTCOMES = 5
MIN_FEATURE_SUPPORT = 2
MAX_ADJUSTMENT = 5.0
FEATURE_SCALE = 2.5


@dataclass(frozen=True)
class FeatureStat:
    feature_type: str
    feature_value: str
    count: int
    mean_outcome: float
    global_mean: float
    adjustment: float

    def to_dict(self) -> dict:
        return {
            "feature_type": self.feature_type,
            "feature_value": self.feature_value,
            "count": self.count,
            "mean_outcome": self.mean_outcome,
            "global_mean": self.global_mean,
            "adjustment": self.adjustment,
        }


@dataclass(frozen=True)
class OutcomeModel:
    sample_count: int
    global_mean: float
    feature_stats: dict[tuple[str, str], FeatureStat]

    @property
    def active(self) -> bool:
        return self.sample_count >= MIN_TOTAL_OUTCOMES


@dataclass(frozen=True)
class OutcomeAdjustment:
    score: float
    reasons: tuple[str, ...]
    sample_count: int


def latest_ranking_at_or_before(
    *,
    session,
    job_id: int,
    profile_name: str,
    at,
):
    return session.scalar(
        select(JobRankingRecord)
        .where(JobRankingRecord.job_id == job_id)
        .where(JobRankingRecord.profile_name == profile_name)
        .where(JobRankingRecord.ranked_at <= at)
        .order_by(
            JobRankingRecord.ranked_at.desc(),
            JobRankingRecord.id.desc(),
        )
        .limit(1)
    )


def application_histories(
    *,
    session,
    profile_name: str,
) -> dict[int, list[JobApplicationEventRecord]]:
    events = session.scalars(
        select(JobApplicationEventRecord)
        .where(JobApplicationEventRecord.profile_name == profile_name)
        .order_by(
            JobApplicationEventRecord.job_id.asc(),
            JobApplicationEventRecord.created_at.asc(),
            JobApplicationEventRecord.id.asc(),
        )
    ).all()

    histories: dict[int, list[JobApplicationEventRecord]] = defaultdict(list)

    for event in events:
        histories[event.job_id].append(event)

    return histories


def build_outcome_model(
    *,
    session,
    profile: CandidateProfile,
) -> OutcomeModel:
    histories = application_histories(
        session=session,
        profile_name=profile.name,
    )

    samples: list[tuple[float, OutcomeFeatures]] = []

    for job_id, events in histories.items():
        historical_outcome = derive_historical_outcome(events)

        if historical_outcome is None:
            continue

        job = session.get(
            JobRecord,
            job_id,
        )

        if job is None:
            continue

        ranking = latest_ranking_at_or_before(
            session=session,
            job_id=job_id,
            profile_name=profile.name,
            at=historical_outcome.applied_at,
        )

        if ranking is None:
            continue

        samples.append(
            (
                historical_outcome.value,
                extract_outcome_features(
                    job=job,
                    ranking=ranking,
                    profile=profile,
                ),
            )
        )

    if not samples:
        return OutcomeModel(
            sample_count=0,
            global_mean=0.0,
            feature_stats={},
        )

    global_mean = sum(outcome for outcome, _ in samples) / len(samples)

    groups: dict[tuple[str, str], list[float]] = defaultdict(list)

    for outcome, features in samples:
        for feature_type, feature_value in features.items():
            groups[(feature_type, feature_value)].append(outcome)

    feature_stats: dict[tuple[str, str], FeatureStat] = {}

    for (feature_type, feature_value), outcomes in groups.items():
        count = len(outcomes)
        mean_outcome = sum(outcomes) / count

        if count < MIN_FEATURE_SUPPORT:
            adjustment = 0.0
        else:
            shrinkage = count / (count + 3.0)
            adjustment = (mean_outcome - global_mean) * FEATURE_SCALE * shrinkage

        adjustment = max(
            -MAX_ADJUSTMENT,
            min(
                MAX_ADJUSTMENT,
                adjustment,
            ),
        )

        feature_stats[(feature_type, feature_value)] = FeatureStat(
            feature_type=feature_type,
            feature_value=feature_value,
            count=count,
            mean_outcome=round(mean_outcome, 4),
            global_mean=round(global_mean, 4),
            adjustment=round(adjustment, 3),
        )

    return OutcomeModel(
        sample_count=len(samples),
        global_mean=round(global_mean, 4),
        feature_stats=feature_stats,
    )


def score_outcome_adjustment(
    *,
    model: OutcomeModel,
    features: OutcomeFeatures,
) -> OutcomeAdjustment:
    if not model.active:
        return OutcomeAdjustment(
            score=0.0,
            reasons=(),
            sample_count=model.sample_count,
        )

    candidates: list[FeatureStat] = []

    for key in features.items():
        stat = model.feature_stats.get(key)

        if stat is None or stat.count < MIN_FEATURE_SUPPORT or stat.adjustment == 0.0:
            continue

        candidates.append(stat)

    candidates.sort(
        key=lambda item: abs(item.adjustment),
        reverse=True,
    )
    selected = candidates[:4]

    if not selected:
        return OutcomeAdjustment(
            score=0.0,
            reasons=(),
            sample_count=model.sample_count,
        )

    raw = sum(item.adjustment for item in selected) / len(selected)
    final = max(
        -MAX_ADJUSTMENT,
        min(MAX_ADJUSTMENT, raw),
    )

    reasons = tuple(
        (
            "Outcome signal "
            f"{item.feature_type}={item.feature_value} "
            f"(n={item.count}, adj={item.adjustment:+.2f})"
        )
        for item in selected
    )

    return OutcomeAdjustment(
        score=round(final, 2),
        reasons=reasons,
        sample_count=model.sample_count,
    )


def top_feature_stats(
    model: OutcomeModel,
    *,
    limit: int = 50,
) -> list[FeatureStat]:
    values = [
        stat
        for stat in model.feature_stats.values()
        if stat.count >= MIN_FEATURE_SUPPORT
    ]

    values.sort(
        key=lambda item: (
            abs(item.adjustment),
            item.count,
        ),
        reverse=True,
    )

    return values[:limit]
