"""
Agent action gateway guarded by policy decisions.
"""

from __future__ import annotations

import datetime as dt
from typing import Awaitable, Callable, Dict

from app.config import Settings
from app.models.agent import AgentActionRequest, AgentActionResponse
from app.models.events import (
    EventContext,
    EventOperation,
    EventResource,
    EventSubject,
    SecurityEvent,
)
from app.opa_client import OPAClient

from .exceptions import PolicyDeniedError

ToolHandler = Callable[[Dict[str, str]], Awaitable[Dict[str, str]]]


class AgentService:
    """Provides a minimal agent action executor backed by policies."""

    def __init__(self, settings: Settings, opa_client: OPAClient) -> None:
        self._settings = settings
        self._opa = opa_client
        self._tool_registry: Dict[str, ToolHandler] = {
            "ping": self._tool_ping,
            "whoami": self._tool_whoami,
        }

    async def execute(self, request: AgentActionRequest) -> AgentActionResponse:
        if request.tool not in self._settings.agent_allowed_tools:
            raise PolicyDeniedError(f"Tool '{request.tool}' is not allowed")

        event = SecurityEvent(
            subject=EventSubject(user_id=request.user or "agent"),
            operation=EventOperation(action="execute", component="agent_gateway"),
            resource=EventResource(type="tool", name=request.tool),
            context=EventContext(metadata=request.input or {}),
        )

        decision = await self._opa.evaluate("agent/allow", event)
        if not decision.allow:
            raise PolicyDeniedError(decision.reason)

        handler = self._tool_registry.get(request.tool)
        if handler is None:
            raise PolicyDeniedError(f"Tool '{request.tool}' is not implemented")

        output = await handler(request.input or {})
        return AgentActionResponse(tool=request.tool, output=output)

    async def _tool_ping(self, _: Dict[str, str]) -> Dict[str, str]:
        return {
            "message": "pong",
            "gateway_time": dt.datetime.utcnow().isoformat() + "Z",
        }

    async def _tool_whoami(self, _: Dict[str, str]) -> Dict[str, str]:
        return {
            "service": self._settings.app_name,
            "policy_backend": self._settings.opa_url,
        }
