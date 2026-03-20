# Pydantic models for API request and response shapes
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    session_id: str = "default"  # used to track conversation history
    namespace: str = "default"


class QueryResponse(BaseModel):
    query: str
    answer: str
    session_id: str


class HealthResponse(BaseModel):
    status: str
    kubernetes: str
    version: str


class ClusterHealthResponse(BaseModel):
    score: int
    status: str
    summary: dict
    issues: list
    ai_analysis: str


class SessionClearResponse(BaseModel):
    session_id: str
    message: str
