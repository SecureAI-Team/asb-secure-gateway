"""
Pydantic representations of the ASB Security Event schema v0.1.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

EVENT_SCHEMA = "asb.security.event/0.1"


class EventSubject(BaseModel):
    user_id: str = "anonymous"
    token_id: str | None = None
    tenant_id: str | None = None
    platform: str = "api"


class EventOperation(BaseModel):
    action: str
    component: str
    model_config = ConfigDict(extra="allow")


class EventResource(BaseModel):
    type: str
    name: str
    model_config = ConfigDict(extra="allow")


class EventContext(BaseModel):
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: Dict[str, str] = Field(default_factory=dict)


class SecurityDecision(BaseModel):
    allow: bool
    reason: str | None = None


class SecurityEvent(BaseModel):
    schema_: str = Field(default=EVENT_SCHEMA, alias="schema")
    subject: EventSubject
    operation: EventOperation
    resource: EventResource
    context: EventContext = Field(default_factory=EventContext)
    decision: Optional[SecurityDecision] = None

    model_config = ConfigDict(populate_by_name=True)

    def with_decision(self, allow: bool, reason: str | None = None) -> "SecurityEvent":
        self.decision = SecurityDecision(allow=allow, reason=reason)
        return self
