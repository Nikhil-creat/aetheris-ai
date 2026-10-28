import os, json, time, hashlib, pathlib
from cryptography.fernet import Fernet
_F = Fernet(os.environ["VAULT_KEY"].encode()) if os.getenv("VAULT_KEY") else None
AUDIT = pathlib.Path(os.getenv("AUDIT_PATH", "/tmp/audit.jsonl"))
def seal(s: str) -> str: return _F.encrypt(s.encode()).decode()
def unseal(s: str) -> str: return _F.decrypt(s.encode()).decode()
def _h(e): return hashlib.sha256(json.dumps(e, sort_keys=True).encode()).hexdigest()
def audit(ev, data):  # tamper-evident hash chain
    try: prev = json.loads(AUDIT.read_text().splitlines()[-1])["h"]
    except Exception: prev = "0" * 64
    e = {"t": int(time.time()), "ev": ev, "d": data, "p": prev}; e["h"] = _h(e)
    with AUDIT.open("a") as f: f.write(json.dumps(e) + "\n")
def verify():
    prev = "0" * 64
    for line in (AUDIT.read_text().splitlines() if AUDIT.exists() else []):
        e = json.loads(line); h = e.pop("h")
        if e["p"] != prev or _h(e) != h: return False
        prev = h
    return True
