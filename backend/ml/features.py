from __future__ import annotations
import numpy as np
import pandas as pd

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Vanilla RSI (bağımlılık eklemeden)"""
    delta = series.diff()
    up = np.where(delta > 0, delta, 0.0)
    down = np.where(delta < 0, -delta, 0.0)
    roll_up = pd.Series(up, index=series.index).ewm(alpha=1/period, adjust=False).mean()
    roll_down = pd.Series(down, index=series.index).ewm(alpha=1/period, adjust=False).mean()
    rs = roll_up / (roll_down + 1e-12)
    return 100 - (100 / (1 + rs))

def build_features(df: pd.DataFrame, horizon: int = 7) -> pd.DataFrame:
    """
    Basit ve hızlı özellik seti:
     - getiri, volatilite, hareketli ortalama, RSI
     - hedef: ileriye dönük yüzde getiri (regresyon) ve/veya yön (sınıflandırma)
    """
    out = df.copy()
    out["ret_1"] = out["close"].pct_change()
    out["ret_5"] = out["close"].pct_change(5)
    out["ret_10"] = out["close"].pct_change(10)
    out["vol_10"] = out["ret_1"].rolling(10).std()
    out["sma_10"] = out["close"].rolling(10).mean()
    out["sma_20"] = out["close"].rolling(20).mean()
    out["rsi_14"] = rsi(out["close"], 14)
    # hedefler
    out[f"y_ret_{horizon}"] = out["close"].pct_change(periods=horizon).shift(-horizon)
    out[f"y_up_{horizon}"] = (out[f"y_ret_{horizon}"] > 0).astype(int)
    out = out.dropna().copy()
    return out

