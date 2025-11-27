"""
LLM proxy service that enforces policies before forwarding to OpenAI.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from app.config import Settings
from app.models.events import (
    EventContext,
    EventOperation,
    EventResource,
    EventSubject,
    SecurityEvent,
)
from app.models.llm import (
    ChatCompletionChoice,
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    UsageMetrics,
)
from app.opa_client import OPAClient

from .exceptions import PolicyDeniedError

logger = logging.getLogger(__name__)


class LLMProxyService:
    """Applies policy checks then proxies to an upstream OpenAI-compatible API."""

    def __init__(self, settings: Settings, opa_client: OPAClient) -> None:
        self._settings = settings
        self._opa = opa_client

    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Forward a chat completion request after running policy checks."""
        if request.stream:
            raise PolicyDeniedError("Streaming is disabled in this demo gateway")

        event = SecurityEvent(
            subject=EventSubject(user_id=request.user or "anonymous"),
            operation=EventOperation(action="chat_completion", component="llm_proxy"),
            resource=EventResource(type="llm", name=request.model),
            context=EventContext(
                metadata={
                    "message_roles": [msg.role for msg in request.messages],
                    "temperature": request.temperature,
                }
            ),
        )

        decision = await self._opa.evaluate("prompt/allow", event)
        if not decision.allow:
            raise PolicyDeniedError(decision.reason)

        if self._settings.openai_api_key:
            return await self._forward_to_openai(request)

        logger.debug("OPENAI_API_KEY not configured, returning demo response")
        return self._demo_response(request)

    async def _forward_to_openai(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Forward the payload to the configured OpenAI-compatible endpoint."""
        base_url = self._settings.openai_base_url.rstrip("/")
        url = f"{base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = request.model_dump(exclude_none=True)
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return ChatCompletionResponse.model_validate(response.json())

    def _demo_response(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Return a deterministic demo response when no upstream is configured."""
        last_user = next(
            (msg.content for msg in reversed(request.messages) if msg.role == "user"),
            "",
        )
        message = ChatCompletionMessage(
            role="assistant",
            content=(
                "This is a demo response from ASB Secure Gateway. "
                "Upstream OpenAI connectivity is disabled; last user message was: "
                f'"{last_user}".'
            ),
        )
        choice = ChatCompletionChoice(index=0, message=message, finish_reason="stop")
        usage = UsageMetrics(
            prompt_tokens=len(request.messages) * 20,
            completion_tokens=len(message.content.split()),
            total_tokens=len(request.messages) * 20 + len(message.content.split()),
        )
        return ChatCompletionResponse(model=request.model, choices=[choice], usage=usage)

