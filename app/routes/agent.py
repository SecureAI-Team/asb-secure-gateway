"""
Agent action execution endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.agent import AgentActionRequest, AgentActionResponse
from app.services.agent_service import AgentService
from app.services.exceptions import PolicyDeniedError
from app.container import get_agent_service

router = APIRouter(prefix="/v1/agent", tags=["agent"])


@router.post(
    "/action/execute",
    response_model=AgentActionResponse,
    summary="Execute a pre-approved agent tool",
)
async def execute_action(
    request: AgentActionRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentActionResponse:
    try:
        return await service.execute(request)
    except PolicyDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": str(exc)},
        ) from exc

