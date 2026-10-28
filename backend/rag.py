import os, re, zlib, math, pathlib
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
D = 256
def embed(t):  # hashed bag-of-words stand-in; swap for Gemini embeddings for true semantics
    v = [0.0] * D
    for w in re.findall(r"[a-z0-9]{3,}", t.lower()): v[zlib.crc32(w.encode()) % D] += 1
    n = math.sqrt(sum(x * x for x in v)) or 1
    return [x / n for x in v]
CH = [c.strip() for p in pathlib.Path(__file__).parent.joinpath("kb").glob("*.md") for c in p.read_text().split("\n\n") if c.strip()]
try:
    _c = QdrantClient(url=os.environ["QDRANT_URL"]) if os.getenv("QDRANT_URL") else QdrantClient(":memory:")
    _c.recreate_collection("kb", vectors_config=VectorParams(size=D, distance=Distance.COSINE))
    _c.upsert("kb", [PointStruct(id=i, vector=embed(t), payload={"text": t}) for i, t in enumerate(CH)])
except Exception: _c = None
def hybrid(q, lexical, k=3):
    out = [c for _, _, c in lexical(q, k)]
    if _c:
        try:
            for h in _c.search("kb", query_vector=embed(q), limit=k):
                if h.payload["text"] not in out and h.score > 0.1: out.append(h.payload["text"])
        except Exception: pass
    return out[:k + 2]
