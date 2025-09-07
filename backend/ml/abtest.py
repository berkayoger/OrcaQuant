from __future__ import annotations
import hashlib
from typing import Optional

def stable_bucket(user_id: str, buckets: int = 2) -> int:
    """Kullanıcıyı deterministik şekilde 0..buckets-1 aralığına atar."""
    h = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
    return int(h[:8], 16) % buckets

def pick_model_variant(user_id: Optional[str]) -> str:
    """
    A/B: user_id verilirse sabit bucket; yoksa kontrol.
    v0: klasik TA; v1: ML (son sürüm).
    """
    if not user_id:
        return "v0"
    b = stable_bucket(user_id, buckets=2)
    return "v1" if b == 1 else "v0"

