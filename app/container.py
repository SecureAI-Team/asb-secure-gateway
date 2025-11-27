"""
Simple dependency container helpers for FastAPI dependencies.
"""

from functools import lru_cache

from app.config import Settings, get_settings
from app.opa_client import OPAClient
from app.services.agent_service import AgentService
from app.services.llm_proxy import LLMProxyService
from app.services.rag_service import RAGService


@lru_cache
def get_opa_client() -> OPAClient:
    return OPAClient(get_settings().opa_url)


@lru_cache
def get_llm_service() -> LLMProxyService:
    return LLMProxyService(get_settings(), get_opa_client())


@lru_cache
def get_rag_service() -> RAGService:
    return RAGService(get_settings(), get_opa_client())


@lru_cache
def get_agent_service() -> AgentService:
    return AgentService(get_settings(), get_opa_client())


def get_config() -> Settings:
    return get_settings()

