"""
Subset of the OpenAI Chat Completions schema used by the proxy.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = "stop"


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: "asb-response")
    object: str = "chat.completion"
    created: int = Field(
        default_factory=lambda: int(datetime.now(tz=timezone.utc).timestamp())
    )
    model: str
    choices: List[ChatCompletionChoice]
