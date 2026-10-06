from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Client-generated conversation id")
    message: str = Field(..., min_length=1, max_length=4000)


class SourceChunk(BaseModel):
    source: str
    snippet: str
    score: float


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceChunk]
    escalate: bool
    confidence: float
    latency_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DocumentIngestResponse(BaseModel):
    filename: str
    chunks_indexed: int
    status: Literal["indexed", "failed"]


class HealthResponse(BaseModel):
    status: str
    vector_store_ready: bool
    documents_indexed: int
