# Aetheris AI - Intelligence Designed To Evolve
Frontend (static, GitHub Pages) + FastAPI backend (Groq + Gemini, RAG, guardrails). Built by Nikhil Chary Sriramoju.

Local: `cp .env.example .env` (add keys) then `docker compose up --build` -> web :8080, api :8000.
Never commit `.env`. Deploy the backend (Render/Fly) with the env vars, then paste its URL in the site's Keys tab.

## v2 modules
Swarm (LangGraph + RLAIF judge) /api/swarm | Hybrid RAG (Qdrant + lexical) | Temporal graph (Neo4j or in-memory) | CNN /api/vision (build ML=1) | MCP /mcp (set MCP_TOKEN) | Fernet vault + hash-chained audit /api/audit/verify | Kyber /api/pqc/kem (needs liboqs) | k8s/aetheris.yaml
Not built yet: ZK proofs, Wasm sandbox, Redis semantic cache, K8s operator, JWT/RBAC.
