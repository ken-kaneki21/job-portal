from pydantic import BaseModel


class Company(BaseModel):
    name: str
    ats: str
    identifier: str
    enabled: bool = True
