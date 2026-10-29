---
id: beecount-mcp-and-docs-index-runtime
scope: project
type: architecture
status: active
tags: [mcp, pat, streamable-http, embeddings, rag, docker]
updated: 2026-09-19
---

# MCP And Embedding Index Runtime Coupling

- MCP is a Streamable HTTP endpoint at both `/api/v1/mcp` and `/api/v1/mcp/` without redirect, configured stateless with JSON responses. The main app must enter and exit FastMCP’s session-manager context during startup/shutdown; route registration must remain before the SPA catch-all.
- MCP authentication is PAT-only with independent `mcp:read`/`mcp:write` scopes. Regular JWT access tokens are rejected on MCP, and MCP PATs are rejected on ordinary API endpoints. Write tools self-call the in-process FastAPI ASGI `/write/*` routes, preserving ordinary validation, idempotency, sync events, and notifications rather than maintaining a second write path.
- The Docker image fetches prebuilt `docs-index.zh.sqlite`/`docs-index.en.sqlite` artifacts from BeeCount-Website at image build time and copies them into `/app/data`. Missing indexes degrade document Q&A; they are image artifacts, not persistent user data under `/data`.
- `EMBEDDING_MODEL` must exactly match the model recorded when the bundled indexes were built. A model mismatch makes cosine similarity semantically invalid even if dimensions match; a dimension mismatch returns no results. Changing provider/model therefore requires rebuilding the Website indexes and the Cloud image together. An absent API key degrades only document Q&A, not accounting or MCP tools.

## Evidence

- `README.md`
- `docker-compose.yml`
- `Dockerfile`
- `src/main.py`
- `src/deps.py`
- `src/mcp/server.py`
- `src/_mcp_internal_client.py`
- `src/services/ai/docs_index.py`
- `tests/test_mcp_streamable_http.py`
- `tests/test_mcp_tools.py`
