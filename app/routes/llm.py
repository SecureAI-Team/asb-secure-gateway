"""
LLM proxy endpoints.
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException

from app.config import Settings, get_settings
from app.models.llm import ChatCompletionRequest, ChatCompletionResponse
from app.services.llm_proxy import handle_chat_completion

router = APIRouter(tags=["llm"])
logger = logging.getLogger(__name__)


@router.post(
    "/v1/chat/completions",
    response_model=ChatCompletionResponse,
    summary="OpenAI-compatible chat completions proxy",
)
async def create_chat_completion(
    request: ChatCompletionRequest,
    settings: Settings = Depends(get_settings),
    user_id: str | None = Header(default=None, alias="X-ASB-User-Id"),
) -> ChatCompletionResponse:
    try:
        return await handle_chat_completion(request, settings, user_id=user_id)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - unexpected bug
        logger.exception("Unexpected error handling chat completion")
        raise HTTPException(
            status_code=500, detail={"message": "Internal server error"}
        ) from exc
