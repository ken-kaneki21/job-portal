import httpx

from jobintel.sources.ashby import AshbySource
from jobintel.sources.base import JobSource
from jobintel.sources.greenhouse import GreenhouseSource
from jobintel.sources.lever import LeverSource
from jobintel.sources.smartrecruiters import SmartRecruitersSource


def build_sources(
    client: httpx.AsyncClient,
) -> dict[str, JobSource]:
    return {
        "greenhouse": GreenhouseSource(client),
        "lever": LeverSource(client),
        "ashby": AshbySource(client),
        "smartrecruiters": SmartRecruitersSource(client),
    }