# Architecture
```mermaid
sequenceDiagram
  participant U as Browser (GitHub Pages)
  participant A as FastAPI gateway
  participant R as Hybrid RAG (Qdrant + lexical)
  participant G as Temporal graph (Neo4j)
  participant L as Groq / Gemini
  U->>A: POST /api/chat or /api/swarm
  A->>A: guard (injection, redaction, rate limit)
  A->>R: retrieve chunks
  A->>G: fetch temporal facts
  A->>L: prompt with context (auto-detected model, failover)
  L-->>A: answer
  A->>A: hash-chained audit entry
  A-->>U: answer + sources
```
## Design decisions
- Static frontend on GitHub Pages; stateful services behind one API so keys stay server-side.
- Provider failover: Groq for short/fast, Gemini for long inputs; either covers the other.
- Retrieval degrades gracefully: Qdrant and Neo4j fall back to in-memory when not configured.
- The swarm is a LangGraph pipeline (sequential fallback) ending in an LLM judge score used as a feedback signal.
