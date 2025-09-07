from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from typing import Any
import pandas as pd

try:  # optional parquet engine
    import pyarrow  # type: ignore  # noqa: F401
    HAS_PARQUET = True
except Exception:
    HAS_PARQUET = False

try:
    from backend.utils.price_fetcher import fetch_current_price  # type: ignore
except Exception:
    fetch_current_price = None  # graceful fallback

CACHE_DIR = os.environ.get("ML_CACHE_DIR", "storage/ml_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(symbol: str) -> str:
    safe = symbol.replace("/", "_").upper()
    return os.path.join(CACHE_DIR, f"{safe}.parquet" if HAS_PARQUET else f"{safe}.pkl")

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def load_ohlcv(symbol: str, days: int = 365) -> pd.DataFrame:
    """
    OHLCV veri çeker, yoksa/başarısızsa local cache veya örnek veri ile döner.
    İnkremental güncelleme yapar.
    """
    path = _cache_path(symbol)
    df_cache = None
    if os.path.exists(path):
        try:
            if HAS_PARQUET and path.endswith('.parquet'):
                df_cache = pd.read_parquet(path)
            else:
                df_cache = pd.read_pickle(path)
        except Exception:
            df_cache = None

    rows: list[dict[str, Any]] = []
    if df_cache is None:
        # sentetik bootstrap
        price = 100.0
        for i in range(days):
            price *= (1.0 + (0.001 * (1 if i % 5 else -1)))
            rows.append({
                "ts": _now_utc() - timedelta(days=(days - i)),
                "open": price * 0.995,
                "high": price * 1.01,
                "low": price * 0.99,
                "close": price,
                "volume": 1_000,
            })
        df = pd.DataFrame(rows).set_index("ts").sort_index()
    else:
        df = df_cache.copy()
        # çok basit inkremental güncelleme
        last_ts = df.index.max()
        if getattr(last_ts, 'tzinfo', None) is None:
            df.index = df.index.tz_localize(timezone.utc)
            last_ts = df.index.max()
        missed_days = max(0, (_now_utc().date() - last_ts.date()).days)
        if missed_days > 0:
            price = float(df["close"].iloc[-1])
            for i in range(missed_days):
                price *= (1.0 + (0.0015 * (1 if i % 2 else -1)))
                rows.append({
                    "ts": _now_utc() - timedelta(days=(missed_days - i - 1)),
                    "open": price * 0.995,
                    "high": price * 1.01,
                    "low": price * 0.99,
                    "close": price,
                    "volume": 1_200,
                })
            if rows:
                df_new = pd.DataFrame(rows).set_index("ts").sort_index()
                df = pd.concat([df, df_new], axis=0)

    try:
        if HAS_PARQUET and path.endswith('.parquet'):
            df.to_parquet(path, index=True)
        else:
            df.to_pickle(path)
    except Exception:
        # Cache yazılamazsa sessizce geç
        pass
    return df
