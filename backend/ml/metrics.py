from __future__ import annotations
from collections import deque
from typing import Deque, Dict

# Basit hafıza içi metrik kolektörü (prod'da DB'ye yazılabilir)
_last_preds: Deque[Dict] = deque(maxlen=5000)

def record_prediction(item: Dict) -> None:
    _last_preds.append(item)

def aggregate() -> Dict[str, float]:
    if not _last_preds:
        return {"count": 0}
    n = len(_last_preds)
    ok = sum(1 for x in _last_preds if x.get("correct") is True)
    return {"count": n, "acc": ok / n if n else 0.0}

