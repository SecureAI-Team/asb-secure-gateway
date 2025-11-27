"""
LLM proxy service that enforces policies before forwarding to OpenAI.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Tuple
from uuid import uuid4

import httpx
from fastapi import HTTPException

from app.config import Settings
from app.models.asb_events import SecurityEventLlmInput
from app.models.llm import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
)
from app.opa_client import evaluate_policy

logger = logging.getLogger(__name__)


async def handle_chat_completion(
    request: ChatCompletionRequest,
    settings: Settings,
    user_id: str | None = None,
) -> ChatCompletionResponse:
    """Evaluate policy and forward the chat completion request upstream."""
    if request.stream:
        raise HTTPException(
            status_code=400, detail={"message": "Streaming responses are not supported"}
        )

    if not settings.openai_api_key:
        raise HTTPException(
            status_code=500,
            detail={"message": "OPENAI_API_KEY is not configured for upstream access"},
        )

    event = _build_security_event(request, settings, user_id)

    try:
        opa_raw = await evaluate_policy("asb/prompt", event.model_dump())
    except httpx.HTTPError as exc:  # pragma: no cover - network failure
        logger.exception("OPA evaluation failed for event %s", event.event_id)
        raise HTTPException(
            status_code=502, detail={"message": "Policy evaluation failed"}
        ) from exc

    allowed, reason = _parse_policy_result(opa_raw)
    if not allowed:
        logger.info("Policy denied event %s: %s", event.event_id, reason)
        raise HTTPException(
            status_code=403,
            detail={"message": reason or "Prompt rejected by policy"},
        )

    logger.info("Policy allowed event %s", event.event_id)
    return await _forward_to_upstream(request, settings)


def _build_security_event(
    request: ChatCompletionRequest, settings: Settings, user_id: str | None
) -> SecurityEventLlmInput:
    now = datetime.now(tz=timezone.utc)
    subject = {"user": {"id": user_id or "anonymous"}}
    operation = {
        "category": "llm_completion",
        "name": "chat_completion",
        "direction": "input",
        "stage": "pre",
        "model": {"name": request.model, "provider": "upstream", "mode": "chat"},
    }
    resource = {
        "llm": {
            "messages": [message.model_dump() for message in request.messages],
        }
    }
    context = {
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }
    return SecurityEventLlmInput(
        event_id=str(uuid4()),
        timestamp=now,
        tenant_id=None,
        app_id=getattr(settings, "app_name", None),
        env=getattr(settings, "app_env", None),
        subject=subject,
        operation=operation,
        resource=resource,
        context={k: v for k, v in context.items() if v is not None},
    )


def _parse_policy_result(response: Dict[str, Any]) -> Tuple[bool, str | None]:
    result_block = response.get("result")
    if result_block is None:
        return False, "Policy returned no decision"
    if isinstance(result_block, bool):
        return result_block, None
    allow = bool(result_block.get("allow", False))
    reason = result_block.get("reason")
    return allow, reason


async def _forward_to_upstream(
    request: ChatCompletionRequest, settings: Settings
) -> ChatCompletionResponse:
    base_url = settings.openai_base_url.rstrip("/")
    url = f"{base_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = request.model_dump(exclude_none=True)
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:  # pragma: no cover - upstream failure
        logger.warning(
            "Upstream chat completion failed: status=%s body=%s",
            exc.response.status_code,
            exc.response.text,
        )
        raise HTTPException(
            status_code=exc.response.status_code,
            detail={"message": "Upstream model error", "upstream_status": exc.response.status_code},
        ) from exc
    except httpx.HTTPError as exc:  # pragma: no cover - network failure
        logger.exception("Upstream chat completion network error")
        raise HTTPException(
            status_code=502, detail={"message": "Failed to reach upstream model"}
        ) from exc

    return _map_response(response.json(), request)


def _map_response(
    payload: Dict[str, Any], request: ChatCompletionRequest
) -> ChatCompletionResponse:
    created_ts = payload.get(
        "created", int(datetime.now(tz=timezone.utc).timestamp())
    )
    raw_choices = payload.get("choices") or []
    choices: list[ChatCompletionChoice] = []
    for idx, choice in enumerate(raw_choices):
        message_payload = choice.get("message") or {}
        message = ChatMessage(
            role=message_payload.get("role", "assistant"),
            content=message_payload.get("content", ""),
        )
        choices.append(
            ChatCompletionChoice(
                index=choice.get("index", idx),
                message=message,
                finish_reason=choice.get("finish_reason"),
            )
        )

    return ChatCompletionResponse(
        id=payload.get("id", f"asb-{uuid4().hex}"),
        created=created_ts,
        model=payload.get("model", request.model),
        choices=choices,
    )

