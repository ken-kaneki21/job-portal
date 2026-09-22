from dataclasses import dataclass

from jobintel.models.job import Job


@dataclass(frozen=True)
class FetchedJob:
    job: Job
    raw: dict
