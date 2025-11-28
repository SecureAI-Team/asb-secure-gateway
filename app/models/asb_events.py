"""
Simplified ASB Security Event models used for LLM policy evaluation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class SecurityEventLlmInput(BaseModel):
    schema_version: Literal["asb-sec-0.1"] = "asb-sec-0.1"
    event_id: str
    timestamp: datetime
    tenant_id: Optional[str] = None
    app_id: Optional[str] = None
    env: Optional[str] = None
    subject: Dict[str, Any] = Field(default_factory=dict)
    operation: Dict[str, Any]
    resource: Dict[str, Any]
    context: Dict[str, Any] = Field(default_factory=dict)
