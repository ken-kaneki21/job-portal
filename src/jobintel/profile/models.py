from pydantic import BaseModel


class CandidateProfile(BaseModel):
    name: str

    target_titles: list[str]
    adjacent_titles: list[str]
    exclude_titles: list[str]

    preferred_locations: list[str]
    allowed_countries: list[str]
    blocked_location_terms: list[str]

    core_skills: list[str]
    secondary_skills: list[str]

    max_preferred_experience_years: int
    hard_max_experience_years: int