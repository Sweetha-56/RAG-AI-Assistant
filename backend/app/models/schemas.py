from typing import Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    file_name: Optional[str] = None


class IngestRequest(BaseModel):
    file_path: str