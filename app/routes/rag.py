"""
Secure RAG gateway endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.rag import RAGSearchRequest, RAGSearchResponse
from app.services.exceptions import PolicyDeniedError
from app.services.rag_service import RAGService
from app.container import get_rag_service

router = APIRouter(prefix="/v1/rag", tags=["rag"])


@router.post(
    "/search_safe",
    response_model=RAGSearchResponse,
    summary="Search pgvector corpus with policy enforcement",
)
async def search_safe(
    request: RAGSearchRequest,
    service: RAGService = Depends(get_rag_service),
) -> RAGSearchResponse:
    try:
        return await service.search(request)
    except PolicyDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": str(exc)},
        ) from exc

