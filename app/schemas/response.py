from pydantic import BaseModel
from typing import List


class HealthResponse(BaseModel):
    status: str

class Source(BaseModel):
    file: str
    page: int

class AskResponse(BaseModel):
    answer: str
    sources: List[Source] = []

class IngestResponse(BaseModel):

    message: str