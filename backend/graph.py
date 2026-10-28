import os
EDGES = [("Gateway","ROUTES_TO","Groq","2026-01"),("Gateway","ROUTES_TO","Gemini","2026-01"),("GraphRAG","USES","Qdrant","2026-02"),
 ("GraphRAG","USES","Neo4j","2026-02"),("Swarm","CONTAINS","Compliance Auditor","2026-03"),("Swarm","CONTAINS","Security Sentinel","2026-03"),
 ("MCP","EXPOSES","Swarm","2026-04"),("Vault","PROTECTS","API keys","2026-05")]
_d = None
if os.getenv("NEO4J_URI"):
    try:
        from neo4j import GraphDatabase
        _d = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.getenv("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"]))
        with _d.session() as s:
            for a, r, b, t in EDGES:
                s.run("MERGE (a:Entity {name:$a}) MERGE (b:Entity {name:$b}) MERGE (a)-[e:REL {type:$r}]->(b) SET e.since=$t", a=a, b=b, r=r, t=t)
    except Exception: _d = None
def facts(q):  # temporal edges: relation + since
    rows = []
    if _d:
        try:
            with _d.session() as s:
                rows = [f"{x['a']} {x['r']} {x['b']} (since {x['t']})" for x in s.run(
                    "MATCH (a:Entity)-[e:REL]->(b:Entity) WHERE toLower($q) CONTAINS toLower(a.name) OR toLower($q) CONTAINS toLower(b.name) "
                    "RETURN a.name a, e.type r, b.name b, e.since t ORDER BY t", q=q)]
        except Exception: rows = []
    ql = q.lower()
    return (rows or [f"{a} {r} {b} (since {t})" for a, r, b, t in EDGES if a.lower() in ql or b.lower() in ql])[:6]
