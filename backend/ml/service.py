from __future__ import annotations
import os
import threading
import joblib
import pandas as pd
from typing import Optional, Dict
from .data import load_ohlcv
from .features import build_features
from .registry import get_model_path

_lock = threading.Lock()
_loaded: Dict[str, Dict[str, object]] = {}
MODEL_NAME = os.environ.get("ML_MODEL_NAME", "oq_return")
HORIZON = int(os.environ.get("ML_HORIZON_DAYS", "7"))

def _ensure_loaded() -> bool:
    with _lock:
        if MODEL_NAME in _loaded:
            return True
        path = get_model_path(MODEL_NAME, None)
        if not path:
            return False
        reg_p = os.path.join(path, "reg.joblib")
        cls_p = os.path.join(path, "cls.joblib")
        if not (os.path.exists(reg_p) and os.path.exists(cls_p)):
            return False
        _loaded[MODEL_NAME] = {
            "reg": joblib.load(reg_p),
            "cls": joblib.load(cls_p),
        }
        return True

def warmup() -> bool:
    return _ensure_loaded()

def predict(symbol: str, user_id: Optional[str] = None) -> Dict:
    """
    Dönenler:
      - y_hat: beklenen yüzde getiri (horizon günü)
      - prob_up: yön sınıflandırma ihtimali
    """
    ok = _ensure_loaded()
    df = load_ohlcv(symbol, days=400)
    feat = build_features(df, horizon=HORIZON)
    X = feat[["ret_1", "ret_5", "ret_10", "vol_10", "sma_10", "sma_20", "rsi_14"]].iloc[[-1]]

    if not ok:
        # ML modeli yoksa basit fallback: son 10 gün ortalamasına göre naive tahmin
        y_hat = float(feat["ret_10"].iloc[-1] or 0.0)
        prob_up = 0.5 + (0.25 if y_hat > 0 else -0.25)
        return {"variant": "v0", "y_hat": y_hat, "prob_up": prob_up}

    reg = _loaded[MODEL_NAME]["reg"]
    cls = _loaded[MODEL_NAME]["cls"]
    # type: ignore[no-any-return]
    y_hat = float(getattr(reg, "predict")(X)[0])
    if hasattr(cls, "predict_proba"):
        prob_up = float(getattr(cls, "predict_proba")(X)[0, 1])
    else:
        prob_up = float(getattr(cls, "predict")(X)[0])
    return {"variant": "v1", "y_hat": y_hat, "prob_up": prob_up}

