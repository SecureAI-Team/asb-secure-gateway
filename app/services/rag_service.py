"""
Secure RAG service guarding access to the demo pgvector corpus.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List

import asyncpg  # type: ignore[import-untyped]

from app.config import Settings
from app.models.events import (
    EventContext,
    EventOperation,
    EventResource,
    EventSubject,
    SecurityEvent,
)
from app.models.rag import (
    RAGSearchRequest,
    RAGSearchResponse,
    RAGSearchResult,
)
from app.opa_client import OPAClient

from .exceptions import PolicyDeniedError

logger = logging.getLogger(__name__)


class RAGService:
    """Performs guarded semantic search against a pgvector-backed table."""

    def __init__(self, settings: Settings, opa_client: OPAClient) -> None:
        self._settings = settings
        self._opa = opa_client
        self._pool: asyncpg.Pool | None = None
        self._pool_lock = asyncio.Lock()

    async def search(self, request: RAGSearchRequest) -> RAGSearchResponse:
        """Search the vector store after evaluating security policies."""
        top_k = request.top_k or self._settings.rag_top_k_default
        event = SecurityEvent(
            subject=EventSubject(user_id="rag-user"),
            operation=EventOperation(action="search", component="rag_gateway"),
            resource=EventResource(type="collection", name=self._settings.rag_table),
            context=EventContext(
                metadata={"top_k": top_k, "query_length": len(request.query)}
            ),
        )

        decision = await self._opa.evaluate("rag/allow", event)
        if not decision.allow:
            raise PolicyDeniedError(decision.reason)

        try:
            rows = await self._query_pgvector(request, top_k)
            results = []
            for row in rows:
                row_dict = dict(row)
                results.append(
                    RAGSearchResult(
                        id=str(row_dict["id"]),
                        content=row_dict[self._settings.rag_text_column],
                        score=float(row_dict["score"]),
                        metadata=row_dict.get(self._settings.rag_metadata_column) or {},
                    )
                )
        except Exception as exc:  # pragma: no cover - demo fallback
            logger.warning("Falling back to demo RAG results: %s", exc)
            results = self._fallback_results(request.query, top_k)

        return RAGSearchResponse(results=results)

    async def _query_pgvector(
        self, request: RAGSearchRequest, top_k: int
    ) -> List[asyncpg.Record]:
        pool = await self._get_pool()
        embedding = request.embedding or self._fake_embed(request.query)
        embedding_literal = "[" + ",".join(f"{value:.4f}" for value in embedding) + "]"

        sql = (
            f"SELECT id, {self._settings.rag_text_column}, "
            f"{self._settings.rag_metadata_column}, "
            f"1 - ({self._settings.rag_vector_column} <=> $1::vector) AS score "
            f"FROM {self._settings.rag_table} "
            f"ORDER BY {self._settings.rag_vector_column} <=> $1::vector "
            "LIMIT $2"
        )

        async with pool.acquire() as connection:
            return await connection.fetch(sql, embedding_literal, top_k)

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            async with self._pool_lock:
                if self._pool is None:
                    self._pool = await asyncpg.create_pool(
                        dsn=self._settings.database_url,
                        min_size=1,
                        max_size=4,
                    )
        return self._pool

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    @staticmethod
    def _fake_embed(text: str, dims: int = 6) -> List[float]:
        # Deterministic toy embedding based on character codes.
        values = [0.0] * dims
        for index, ch in enumerate(text[: dims * 4]):
            values[index % dims] += (ord(ch) % 32) / 100.0
        return values

    def _fallback_results(self, query: str, top_k: int) -> List[RAGSearchResult]:
        base_content = "Demo knowledge base entry related to"
        return [
            RAGSearchResult(
                id=f"demo-{idx}",
                content=f"{base_content} '{query}' #{idx}",
                score=1.0 - (idx * 0.1),
                metadata={"source": "demo-fallback"},
            )
            for idx in range(min(top_k, 3))
        ]
