from jobintel.broad_search import (
    MAX_SEARCHES,
    SearchSpec,
    build_profile_searches,
    normalize_location,
    preferred_search_locations,
)
from jobintel.profile.models import (
    CandidateProfile,
)


def make_profile() -> CandidateProfile:
    return CandidateProfile(
        name="universal",
        target_titles=[
            "data engineer",
            "senior data engineer",
            "data analyst",
            "business data analyst",
        ],
        adjacent_titles=[
            "analytics engineer",
            "data platform engineer",
            "ai engineer",
        ],
        exclude_titles=[
            "director",
            "vp",
        ],
        preferred_locations=[
            "Bengaluru",
            "Bangalore",
            "Hyderabad",
        ],
        allowed_countries=[
            "India",
        ],
        blocked_location_terms=[],
        core_skills=[
            "Python",
            "SQL",
            "Snowflake",
            "Airflow",
        ],
        secondary_skills=[
            "dbt",
            "Azure",
        ],
        max_preferred_experience_years=7,
        hard_max_experience_years=10,
    )


def test_normalize_bengaluru_to_bangalore():
    assert normalize_location("Bengaluru") == "Bangalore"


def test_preferred_locations_are_deduplicated():
    profile = make_profile()

    assert preferred_search_locations(profile) == [
        "Bangalore",
        "Hyderabad",
    ]


def test_profile_searches_include_primary_roles():
    searches = build_profile_searches(make_profile())

    queries = {search.query for search in searches}

    assert "data engineer" in queries

    assert "data analyst" in queries


def test_profile_searches_include_adjacent_roles():
    searches = build_profile_searches(make_profile())

    queries = {search.query for search in searches}

    assert "analytics engineer" in queries

    assert "data platform engineer" in queries


def test_profile_searches_include_skill_queries():
    searches = build_profile_searches(make_profile())

    queries = {search.query.lower() for search in searches}

    assert "python data engineer" in queries

    assert "sql data engineer" in queries

    assert "snowflake data engineer" in queries


def test_search_plan_is_capped():
    profile = make_profile()

    profile.target_titles = [f"primary role {index}" for index in range(20)]

    profile.adjacent_titles = [f"adjacent role {index}" for index in range(20)]

    searches = build_profile_searches(profile)

    assert len(searches) <= MAX_SEARCHES


def test_search_pairs_are_unique():
    searches = build_profile_searches(make_profile())

    pairs = [
        (
            search.query.lower(),
            search.location.lower(),
        )
        for search in searches
    ]

    assert len(pairs) == len(set(pairs))


def test_search_spec_is_immutable():
    search = SearchSpec(
        query="data engineer",
        location="Bangalore",
    )

    assert search.query == "data engineer"

    assert search.location == "Bangalore"
