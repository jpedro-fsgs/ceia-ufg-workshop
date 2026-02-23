from typing import Dict, List

from pydantic import BaseModel


class IngestRequest(BaseModel):
    texts: List[str]
    source: str = "user_upload"


class IngestResponse(BaseModel):
    collection: str
    inserted: int


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3


class SearchResponse(BaseModel):
    results: List[Dict]


class AskRequest(BaseModel):
    question: str
    top_k: int = 3


class AskResponse(BaseModel):
    answer: str
    context: List[Dict]
    # Educational fields
    retrieved_docs: List[Dict] # Rich list of docs with scores
    built_prompt: str         # The exact prompt sent to LLM
