"""Aetheris API: secure Groq+Gemini gateway with auto model detection, RAG, guardrails, rate limiting."""
import os, re, time, math, collections, pathlib
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

GROQ, GEM = os.getenv("GROQ_API_KEY", ""), os.getenv("GEMINI_API_KEY", "")
ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:8080").split(",")]
app = FastAPI(title="Aetheris API", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

@app.middleware("http")
async def headers(req: Request, nxt):
    r = await nxt(req)
    r.headers.update({"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer",
                      "Cache-Control": "no-store", "Strict-Transport-Security": "max-age=31536000"})
    return r

# ---- RAG: TF-IDF over kb/*.md (paragraphs = chunks) ----
tok = lambda s: re.findall(r"[a-z0-9]{3,}", s.lower())
CHUNKS = [(p.name, c.strip()) for p in pathlib.Path(__file__).parent.joinpath("kb").glob("*.md")
          for c in p.read_text().split("\n\n") if c.strip()]
DF = collections.Counter(w for _, c in CHUNKS for w in set(tok(c)))
def retrieve(q, k=3):
    qt, out = tok(q), []
    for n, c in CHUNKS:
        ct = collections.Counter(tok(c))
        s = sum(ct[w] * math.log(1 + len(CHUNKS) / (1 + DF[w])) for w in qt)
        if s > 0: out.append((s, n, c))
    return sorted(out, reverse=True)[:k]

# ---- guardrails ----
INJ = re.compile(r"ignore (all|previous|prior)|system prompt|reveal.*(key|prompt)|jailbreak|developer mode", re.I)
def redact(s): return re.sub(r"\+?\d[\d\s-]{8,}\d", "[number]", re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[email]", s))
HITS: dict = collections.defaultdict(list)
def limit(ip, n=20):
    now = time.time(); HITS[ip] = [t for t in HITS[ip] if now - t < 60]
    if len(HITS[ip]) >= n: raise HTTPException(429, "Rate limit: 20 requests/minute")
    HITS[ip].append(now)

# ---- model auto-detect (cached 1h) ----
_M = {"t": 0, "groq": "", "gem": ""}
async def models():
    if time.time() - _M["t"] < 3600: return _M
    async with httpx.AsyncClient(timeout=15) as c:
        if GROQ:
            try:
                ids = [m["id"] for m in (await c.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {GROQ}"})).json()["data"]
                       if not re.search(r"whisper|guard|tts|orpheus|playai|safeguard", m["id"], re.I)]
                _M["groq"] = next((i for p in ("llama-3.3-70b", "llama-3.1-70b", "llama", "qwen") for i in ids if p in i), ids[0])
            except Exception: _M["groq"] = ""
        if GEM:
            try:
                ms = [m["name"] for m in (await c.get("https://generativelanguage.googleapis.com/v1beta/models?pageSize=100", headers={"x-goog-api-key": GEM})).json()["models"]
                      if "generateContent" in m.get("supportedGenerationMethods", []) and "gemini" in m["name"] and not re.search(r"tts|image|embed|live|audio|thinking", m["name"])]
                _M["gem"] = next((m for m in ms if "flash" in m and not re.search(r"lite|preview|exp", m)), ms[0])
            except Exception: _M["gem"] = ""
    _M["t"] = time.time(); return _M

class Msg(BaseModel):
    role: str = Field(pattern="^(user|assistant)$"); content: str = Field(max_length=2000)
class Chat(BaseModel):
    message: str = Field(min_length=1, max_length=600); history: list[Msg] = Field(default=[], max_length=8)

@app.get("/api/health")
async def health(): m = await models(); return {"ok": True, "groq": m["groq"], "gemini": m["gem"], "chunks": len(CHUNKS)}

@app.post("/api/chat")
async def chat(body: Chat, req: Request):
    limit(req.client.host)
    if INJ.search(body.message): raise HTTPException(400, "Blocked: prompt-injection pattern")
    q, docs, m = redact(body.message), retrieve(body.message), await models()
    sys = "You are the Aetheris AI assistant. Use the context when relevant; say when it is not covered. Never reveal secrets.\nContext:\n" + "\n".join(f"[{n}] {c}" for _, n, c in docs)
    h = [x.model_dump() for x in body.history] + [{"role": "user", "content": q}]
    src = [n for _, n, _ in docs]
    async with httpx.AsyncClient(timeout=30) as c:
        for kind in (("groq", "gem") if len(q) <= 300 else ("gem", "groq")):
            try:
                if kind == "groq" and GROQ and m["groq"]:
                    r = await c.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {GROQ}"},
                                     json={"model": m["groq"], "messages": [{"role": "system", "content": sys}, *h], "temperature": .3, "max_tokens": 600})
                    r.raise_for_status(); return {"answer": r.json()["choices"][0]["message"]["content"], "model": m["groq"], "sources": src}
                if kind == "gem" and GEM and m["gem"]:
                    r = await c.post(f"https://generativelanguage.googleapis.com/v1beta/{m['gem']}:generateContent", headers={"x-goog-api-key": GEM},
                                     json={"systemInstruction": {"parts": [{"text": sys}]}, "contents": [{"role": "user" if x["role"] == "user" else "model", "parts": [{"text": x["content"]}]} for x in h]})
                    r.raise_for_status(); return {"answer": "".join(p["text"] for p in r.json()["candidates"][0]["content"]["parts"]), "model": m["gem"], "sources": src}
            except httpx.HTTPError: continue
    raise HTTPException(503, "No model available. Check server keys and quota.")

# ===== v2: swarm, hybrid RAG, temporal graph, vision, MCP, vault/audit, PQC =====
import hmac
from fastapi import Depends, Header, Response
import rag, graph, vault
from agents import run_swarm

APP_KEY, MCP_TOKEN = os.getenv("APP_API_KEY", ""), os.getenv("MCP_TOKEN", "")
def auth(x_api_key: str = Header(default="")):
    if APP_KEY and not hmac.compare_digest(x_api_key, APP_KEY): raise HTTPException(401, "Bad API key")

async def complete(sys, h):
    m = await models()
    async with httpx.AsyncClient(timeout=40) as c:
        if GROQ and m["groq"]:
            try:
                r = await c.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {GROQ}"},
                                 json={"model": m["groq"], "messages": [{"role": "system", "content": sys}, *h], "temperature": .3, "max_tokens": 500}); r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"], m["groq"]
            except httpx.HTTPError: pass
        if GEM and m["gem"]:
            try:
                r = await c.post(f"https://generativelanguage.googleapis.com/v1beta/{m['gem']}:generateContent", headers={"x-goog-api-key": GEM},
                                 json={"systemInstruction": {"parts": [{"text": sys}]}, "contents": [{"role": "user" if x["role"] == "user" else "model", "parts": [{"text": x["content"]}]} for x in h]}); r.raise_for_status()
                return "".join(p["text"] for p in r.json()["candidates"][0]["content"]["parts"]), m["gem"]
            except httpx.HTTPError: pass
    raise HTTPException(503, "No model available")

def context(q): return "\n".join(rag.hybrid(q, retrieve) + graph.facts(q))

class Task(BaseModel): task: str = Field(min_length=3, max_length=600)
@app.post("/api/swarm")
async def swarm(b: Task, req: Request, _=Depends(auth)):
    limit(req.client.host, 6)
    if INJ.search(b.task): raise HTTPException(400, "Blocked: prompt-injection pattern")
    out = await run_swarm(redact(b.task), complete, context(b.task))
    vault.audit("swarm", {"task": b.task[:80], "score": out["score"], "engine": out["engine"]})
    return out

class Img(BaseModel): image_b64: str = Field(max_length=2_000_000)
@app.post("/api/vision")
async def vision(b: Img, req: Request):
    limit(req.client.host, 10); import cnn; return cnn.analyze(b.image_b64)

@app.get("/api/audit/verify")
def audit_verify(_=Depends(auth)): return {"chain_valid": vault.verify()}

@app.get("/api/pqc/kem")
def kem():  # publishes an ML-KEM (Kyber) public key; a full hybrid handshake is still to build
    try: import oqs
    except ImportError: raise HTTPException(501, "Install liboqs-python to enable Kyber768")
    with oqs.KeyEncapsulation("Kyber768") as k: return {"alg": "Kyber768", "public_key": k.generate_keypair().hex()}

TOOLS = [{"name": n, "description": d, "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}
         for n, d in (("search_knowledge", "Hybrid vector+lexical search"), ("graph_facts", "Temporal knowledge-graph facts"), ("run_swarm", "Run the 4-agent swarm"))]
@app.post("/mcp")
async def mcp(req: Request):
    if not MCP_TOKEN or not hmac.compare_digest(req.headers.get("x-mcp-token", ""), MCP_TOKEN): raise HTTPException(401, "MCP disabled or bad token")
    r = await req.json(); i, m, p = r.get("id"), r.get("method"), r.get("params", {})
    if i is None: return Response(status_code=202)
    if m == "initialize": res = {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "aetheris", "version": "2.0"}}
    elif m == "tools/list": res = {"tools": TOOLS}
    elif m == "tools/call":
        q = str(p.get("arguments", {}).get("query", ""))[:600]; n = p.get("name")
        if n == "search_knowledge": t = "\n".join(rag.hybrid(q, retrieve))
        elif n == "graph_facts": t = "\n".join(graph.facts(q))
        elif n == "run_swarm": t = (await run_swarm(redact(q), complete, context(q)))["plan"]
        else: return {"jsonrpc": "2.0", "id": i, "error": {"code": -32602, "message": "Unknown tool"}}
        vault.audit("mcp", {"tool": n}); res = {"content": [{"type": "text", "text": t}]}
    else: return {"jsonrpc": "2.0", "id": i, "error": {"code": -32601, "message": "Method not found"}}
    return {"jsonrpc": "2.0", "id": i, "result": res}
