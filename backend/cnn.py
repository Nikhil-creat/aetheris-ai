import base64, io
from fastapi import HTTPException
def analyze(b64):
    try:
        import torch, torch.nn as nn, numpy as np
        from PIL import Image
    except ImportError: raise HTTPException(501, "Build with ML=1 (requirements-ml.txt)")
    try: im = Image.open(io.BytesIO(base64.b64decode(b64.split(",")[-1]))).convert("L").resize((128, 128))
    except Exception: raise HTTPException(400, "Invalid image")
    x = torch.tensor(np.asarray(im), dtype=torch.float32)[None, None] / 255
    torch.manual_seed(0)
    net = nn.Sequential(nn.Conv2d(1, 8, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(8, 16, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool2d(1))
    with torch.no_grad(): f = net(x).flatten()
    ed = (x[..., 1:] - x[..., :-1]).abs().mean().item()
    return {"features": [round(v, 4) for v in f.tolist()], "edge_density": round(ed, 4), "anomaly": ed > 0.15, "note": "Untrained demo CNN; load your trained weights for real detection."}
