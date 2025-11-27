"""
LLM proxy endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.llm import ChatCompletionRequest, ChatCompletionResponse
from app.services.exceptions import PolicyDeniedError
from app.services.llm_proxy import LLMProxyService
from app.container import get_llm_service

router = APIRouter(prefix="/v1", tags=["llm"])


@router.post(
    "/chat/completions",
    response_model=ChatCompletionResponse,
    summary="OpenAI-compatible chat completions proxy",
)
async def create_chat_completion(
    request: ChatCompletionRequest,
    service: LLMProxyService = Depends(get_llm_service),
) -> ChatCompletionResponse:
    try:
        return await service.chat_completion(request)
    except PolicyDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": str(exc)},
        ) from exc

