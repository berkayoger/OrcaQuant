from __future__ import annotations
import os
import joblib
import numpy as np
import pandas as pd
from typing import Tuple, Dict
from datetime import datetime

from .data import load_ohlcv
from .features import build_features
from .registry import register_model_local

try:
    import lightgbm as lgb  # type: ignore
except Exception:
    lgb = None
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import r2_score, accuracy_score
from sklearn.model_selection import TimeSeriesSplit

MODEL_NAME = os.environ.get("ML_MODEL_NAME", "oq_return")
HORIZON = int(os.environ.get("ML_HORIZON_DAYS", "7"))
OUT_DIR = os.environ.get("ML_ARTIFACT_DIR", "storage/models")
os.makedirs(OUT_DIR, exist_ok=True)

def _split_xy(df: pd.DataFrame, horizon: int) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    feats = ["ret_1", "ret_5", "ret_10", "vol_10", "sma_10", "sma_20", "rsi_14"]
    X = df[feats].copy()
    y_reg = df[f"y_ret_{horizon}"].copy()
    y_cls = df[f"y_up_{horizon}"].copy()
    return X, y_reg, X, y_cls

def train(symbol: str, horizon: int = HORIZON) -> Dict[str, float]:
    df = load_ohlcv(symbol=symbol, days=540)
    feat = build_features(df, horizon=horizon)
    X, y_reg, X_cls, y_cls = _split_xy(feat, horizon)
    # temporal split
    tss = TimeSeriesSplit(n_splits=5)
    reg_scores, cls_scores = [], []
    reg_model, cls_model = None, None
    for train_idx, test_idx in tss.split(X):
        Xtr, Xte = X.iloc[train_idx], X.iloc[test_idx]
        ytr, yte = y_reg.iloc[train_idx], y_reg.iloc[test_idx]
        if lgb:
            reg_model = lgb.LGBMRegressor(n_estimators=200, learning_rate=0.05, subsample=0.9, colsample_bytree=0.9)
        else:
            reg_model = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
        reg_model.fit(Xtr, ytr)
        yhat = reg_model.predict(Xte)
        reg_scores.append(r2_score(yte, yhat))
    # tek seferde sınıflandırma (daha hızlı)
    if lgb:
        cls_model = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, subsample=0.9, colsample_bytree=0.9)
    else:
        cls_model = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
    cls_model.fit(X_cls, y_cls)
    cls_scores.append(accuracy_score(y_cls, cls_model.predict(X_cls)))

    # kayıt
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    version = f"v{ts}"
    out_dir = os.path.join(OUT_DIR, MODEL_NAME, version)
    os.makedirs(out_dir, exist_ok=True)
    joblib.dump(reg_model, os.path.join(out_dir, "reg.joblib"))
    joblib.dump(cls_model, os.path.join(out_dir, "cls.joblib"))
    metrics = {"r2_mean": float(np.mean(reg_scores)), "acc_cls": float(np.mean(cls_scores))}
    register_model_local(MODEL_NAME, version, out_dir, metrics)
    return metrics

