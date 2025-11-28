"""
FastAPI application entrypoint for the ASB Secure Gateway.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.container import get_agent_service, get_opa_client, get_rag_service
from app.routes import agent, llm, rag

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    logger.info("Starting %s", settings.app_name)
    # Prime singletons so we can close them later.
    get_rag_service()
    get_agent_service()
    try:
        yield
    finally:
        await get_rag_service().close()
        await get_opa_client().close()
        logger.info("Shutdown complete")


app = FastAPI(
    title="ASB Secure Gateway",
    version="0.1.0",
    description="Reference implementation of an AI security gateway powered by OPA.",
    lifespan=lifespan,
)

app.include_router(llm.router)
app.include_router(rag.router)
app.include_router(agent.router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}
