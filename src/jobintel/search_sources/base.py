from abc import ABC, abstractmethod

from jobintel.models.fetched_job import FetchedJob


class SearchSource(ABC):

    @abstractmethod
    async def search_jobs(
        self,
        *,
        query: str,
        location: str | None = None,
        max_pages: int = 1,
    ) -> list[FetchedJob]:
        raise NotImplementedError