from abc import ABC, abstractmethod

from jobintel.models.company import Company
from jobintel.models.fetched_job import FetchedJob


class JobSource(ABC):

    @abstractmethod
    async def fetch_jobs(
        self,
        company: Company,
    ) -> list[FetchedJob]:
        raise NotImplementedError