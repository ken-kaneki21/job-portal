from types import SimpleNamespace

from jobintel.rank import (
    classify_result,
)


def make_result(
    *,
    experience=None,
    experience_score=10,
    score=80,
    sources=None,
):
    return SimpleNamespace(
        detected_experience=experience,
        experience_score=experience_score,
        score=score,
        sources=sources or [],
    )


def test_five_year_role_is_stretch():
    result = make_result(
        experience=5,
        experience_score=4,
        sources=["greenhouse"],
    )

    assert (
        classify_result(result)
        == "stretch"
    )


def test_direct_good_role_is_high_confidence():
    result = make_result(
        experience=3,
        experience_score=10,
        score=80,
        sources=["greenhouse"],
    )

    assert (
        classify_result(result)
        == "high_confidence"
    )


def test_aggregator_role_is_discovery():
    result = make_result(
        experience=3,
        experience_score=10,
        score=80,
        sources=["adzuna"],
    )

    assert (
        classify_result(result)
        == "discovery"
    )


def test_unclear_experience_not_stretch():
    result = make_result(
        experience=None,
        experience_score=1,
        score=75,
        sources=["adzuna"],
    )

    assert (
        classify_result(result)
        == "discovery"
    )