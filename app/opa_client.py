"""
Lightweight async client for communicating with the co-located OPA instance.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from app.config import get_settings
from .models.events import SecurityEvent

logger = logging.getLogger(__name__)


class OPADecision:
    """Container for results returned by OPA policies."""

    def __init__(self, allow: bool, reason: str | None = None, raw: Any | None = None):
        self.allow = allow
        self.reason = reason
        self.raw = raw

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"OPADecision(allow={self.allow}, reason={self.reason})"


class OPAClient:
    """Minimal HTTP client for posting ASB events to OPA."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0))

    async def evaluate(self, policy_path: str, event: SecurityEvent) -> OPADecision:
        """
        Send an evaluation request to OPA.

        Args:
            policy_path: Path under /v1/data/, e.g. "prompt/allow".
            event: Security event payload following ASB schema.
        """
        url = f"{self._base_url}/v1/data/{policy_path.lstrip('/')}"
        payload: Dict[str, Any] = {"input": event.model_dump()}
        logger.debug("Sending event to OPA %s", url)

        response = await self._client.post(url, json=payload)
        response.raise_for_status()

        data = response.json().get("result", {})
        if isinstance(data, bool):
            return OPADecision(allow=data, raw=data)

        allow = bool(data.get("allow", False))
        reason = data.get("reason")
        return OPADecision(allow=allow, reason=reason, raw=data)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()


async def evaluate_policy(path: str, input_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate an OPA policy by posting the provided event as input.

    Args:
        path: Policy path under /v1/data (e.g. "asb/prompt").
        input_event: Serialized security event payload.
    """
    settings = get_settings()
    base_url = settings.opa_url.rstrip("/")
    url = f"{base_url}/v1/data/{path.lstrip('/')}"
    logger.debug("Evaluating OPA policy at %s", url)

    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0)) as client:
        response = await client.post(url, json={"input": input_event})
        response.raise_for_status()
        return response.json()
