"""
Models for the agent action execution API.
"""

from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel


class AgentActionRequest(BaseModel):
    tool: str
    input: Dict[str, str] | None = None
    user: Optional[str] = None


class AgentActionResponse(BaseModel):
    tool: str
    output: Dict[str, str]
    status: str = "success"
