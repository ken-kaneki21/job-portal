from datetime import datetime

from pydantic import BaseModel, HttpUrl


class Job(BaseModel):
    source: str
    source_identifier: str
    external_id: str

    company: str
    title: str

    location: str | None = None
    description: str | None = None
    department: str | None = None

    apply_url: HttpUrl

    posted_at: datetime | None = None
    updated_at: datetime | None = None

    fingerprint: str
