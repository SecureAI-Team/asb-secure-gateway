"""
Models for the secure RAG search API.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RAGSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = None
    embedding: Optional[List[float]] = None


class RAGSearchResult(BaseModel):
    id: str
    content: str
    score: float
    metadata: Dict[str, str] = Field(default_factory=dict)


class RAGSearchResponse(BaseModel):
    results: List[RAGSearchResult]

