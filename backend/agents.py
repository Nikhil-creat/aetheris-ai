import re
ROLES = {"Compliance Auditor": "Check the task against policy, privacy and regulatory risks.",
         "Security Sentinel": "Find security threats and give concrete mitigations.",
         "FinOps Optimizer": "Find cost, token and quota savings.",
         "Neural Architect": "Propose model, retrieval and architecture changes."}
async def run_swarm(task, complete, ctx):
    async def step(name, notes):
        t, _ = await complete(f"You are the {name}. {ROLES[name]} Reply with at most 4 short bullets. Context:\n{ctx}",
                              [{"role": "user", "content": task + "\n\nColleague notes:\n" + "\n".join(notes)}])
        return t
    notes = []
    try:
        from typing import TypedDict
        from langgraph.graph import StateGraph, END
        class S(TypedDict): notes: list[str]
        g, names = StateGraph(S), list(ROLES)
        def mk(n):
            async def f(s): return {"notes": s["notes"] + [f"{n}: {await step(n, s['notes'])}"]}
            return f
        for n in names: g.add_node(n, mk(n))
        g.set_entry_point(names[0])
        for a, b in zip(names, names[1:]): g.add_edge(a, b)
        g.add_edge(names[-1], END)
        notes = (await g.compile().ainvoke({"notes": []}))["notes"]; engine = "langgraph"
    except ImportError:
        for n in ROLES: notes.append(f"{n}: {await step(n, notes)}")
        engine = "sequential"
    plan, model = await complete("Merge the specialist notes into one action plan with 5 numbered steps.",
                                 [{"role": "user", "content": task + "\n\n" + "\n".join(notes)}])
    j, _ = await complete("Rate the plan 1-10 for correctness and usefulness. Reply exactly: SCORE: n", [{"role": "user", "content": plan}])  # RLAIF judge
    m = re.search(r"SCORE:\s*(\d+)", j)
    return {"engine": engine, "notes": notes, "plan": plan, "score": int(m.group(1)) if m else None, "model": model}
