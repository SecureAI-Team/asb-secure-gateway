# ASB Secure Gateway

![CI](https://github.com/SecureAI-Team/asb-secure-gateway/actions/workflows/ci.yml/badge.svg)

Minimal FastAPI + OPA reference that demonstrates:

- OpenAI-compatible `/v1/chat/completions` proxy guarded by prompt policies.
- `/v1/rag/search_safe` endpoint backed by Postgres + pgvector with safety checks.
- `/v1/agent/action/execute` minimal agent tool executor with policy enforcement.
- ASB Security Schema events shipped to OPA as `input` for every operation.
- Single docker-compose stack (API + Postgres/pgvector + OPA).

## Stack

- Python 3.11, FastAPI, Uvicorn
- Postgres `pgvector/pgvector:pg16` demo corpus (`docker/init/01_init.sql`)
- Open Policy Agent sidecar loading `policies/*.rego`

## Running the stack

1. Export environment variables (or create an `.env`) - defaults already match docker-compose:
   ```bash
   # PowerShell examples; replace with export for other shells
   setx OPA_URL http://opa:8181
   setx DATABASE_URL postgresql://postgres:postgres@postgres:5432/asb_gateway
   setx OPENAI_API_KEY ""   # optional, leave empty for demo responses
   ```
2. Build + start everything:
   ```bash
   docker-compose up --build
   ```
3. API is available at `http://localhost:8000` (Swagger UI at `/docs`), OPA at `http://localhost:8181`, Postgres at `localhost:5432`.

## Key endpoints

| Endpoint | Description | Notes |
| --- | --- | --- |
| `POST /v1/chat/completions` | OpenAI-compatible chat completions | Streams disabled; forwards to OpenAI when `OPENAI_API_KEY` is set, otherwise returns deterministic demo text. |
| `POST /v1/rag/search_safe` | Secure RAG search | Queries pgvector table `documents` with dimensionality 6. Falls back to demo data if DB unavailable. |
| `POST /v1/agent/action/execute` | Agent action gateway | Restricts execution to `AGENT_ALLOWED_TOOLS` env var (defaults: `ping`,`whoami`). |
| `GET /health` | Health probe | Returns `{ "status": "ok" }`. |

All routes emit ASB Security Schema v0.1 events (subject / operation / resource / context / decision) and expect an `allow` decision from OPA under:

- `data.prompt.allow`
- `data.rag.allow`
- `data.agent.allow`

See `policies/*.rego` for the minimal guardrails (temperature caps, top_k limits, denied tools, etc.). Modify those files and OPA will live-reload thanks to the shared volume.

## Local development

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Set `DATABASE_URL` to point at a Postgres instance with pgvector + the `documents` table. The dockerized Postgres already includes sample rows and the required `vector` extension.

## Project layout

```
app/
  config.py        # Pydantic settings
  main.py          # FastAPI entrypoint + lifespan hooks
  opa_client.py    # Async HTTP client used by services
  models/          # ASB event + request/response schemas
  routes/          # Thin FastAPI routers per feature
  services/        # Policy-aware service layer
policies/          # prompt/rag/agent rego policies
docker/init/       # pgvector bootstrap SQL
```

## Useful environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `OPA_URL` | `http://opa:8181` | Location of the OPA server |
| `DATABASE_URL` | `postgresql://postgres:postgres@postgres:5432/asb_gateway` | Postgres DSN for RAG search |
| `OPENAI_API_KEY` | `""` | Optional upstream OpenAI API key |
| `OPENAI_BASE_URL` | `https://api.openai.com` | Overridable base URL |
| `AGENT_ALLOWED_TOOLS` | `ping,whoami` | Comma-separated list of allowed agent tools |

## Testing the APIs

```bash
# Chat (demo response unless OPENAI_API_KEY is supplied)
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hello"}]}'

# RAG search
curl -s http://localhost:8000/v1/rag/search_safe \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the gateway?"}'

# Agent tool
curl -s http://localhost:8000/v1/agent/action/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"ping"}'
```

Looking for commercial support, enterprise-specific rules, or expanded policies? Reach out via GitHub discussions or email the maintainer to discuss commercial licensing and premium rule packs.
