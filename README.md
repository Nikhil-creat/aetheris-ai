# Aetheris AI - Intelligence Designed To Evolve
[![CI](https://github.com/Nikhil-creat/aetheris-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/Nikhil-creat/aetheris-ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Sovereign multi-modal agentic AI platform: a Groq + Gemini gateway with automatic model detection, hybrid RAG, a temporal knowledge graph, a LangGraph agent swarm, CNN vision, an MCP server and a zero-trust security layer.
**Live demo:** https://nikhil-creat.github.io/aetheris-ai/

## Features
| Area | What it does |
|---|---|
| Gateway | Auto-detects current Groq and Gemini models, fails over between them |
| RAG | Qdrant vectors + keyword search, with sources returned |
| Graph | Temporal edges (relation + since) in Neo4j or in-memory |
| Agents | Four-role LangGraph swarm and an LLM judge score |
| Vision | PyTorch CNN feature maps (optional build) and an in-browser Sobel demo |
| MCP | JSON-RPC tools for Claude Desktop / Cursor, token-protected |
| Security | CSP, guardrails, rate limits, encrypted vault, tamper-evident audit log |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [SECURITY.md](SECURITY.md).

## Quick start
```
cp .env.example .env      # add GROQ_API_KEY and GEMINI_API_KEY
docker compose up --build # web :8080, api :8000
cd backend && python -m pytest -q
```
Frontend only: open `frontend/index.html`, add a key under Keys.

## API
`GET /api/health` | `POST /api/chat` | `POST /api/swarm` | `POST /api/vision` | `GET /api/audit/verify` | `GET /api/pqc/kem` | `POST /mcp`

## Configuration
`GROQ_API_KEY`, `GEMINI_API_KEY`, `ALLOWED_ORIGINS`, `APP_API_KEY`, `MCP_TOKEN`, `VAULT_KEY`, `QDRANT_URL`, `NEO4J_URI`, `NEO4J_PASSWORD`.

## Roadmap
Not built yet: zero-knowledge proofs, Wasm sandbox, Redis semantic cache, Kubernetes operator, JWT/RBAC, semantic embeddings.

## Author
Nikhil Chary Sriramoju - B.Tech CSE, Vaagdevi College of Engineering. MIT licensed.
