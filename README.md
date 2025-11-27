# asb-secure-gateway (Minimal Core)

> A minimal reference AI security gateway implementing **ASB Security Schema** + OPA.

Features:

- 🔐 **OpenAI-compatible LLM proxy** at `/v1/chat/completions` (demo response)
- 📚 **Secure RAG gateway** at `/v1/rag/search_safe` (with SQLite demo corpus)
- 🤖 **Agent action gateway** at `/v1/agent/action/execute` (simulated tools)
- 🧩 Uses **ASB Security Schema** events + **OPA (Rego)** for policy decisions
- 🐳 Single-node, single-tenant, **Docker Compose one-command up**

## Quick Start

```bash
cp .env.example .env
docker-compose up --build
