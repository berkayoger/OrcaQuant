"""Synthetic payload generators for functional tests."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict


def user_payload(index: int = 1) -> Dict[str, str]:
    return {
        "email": f"user{index}@example.com",
        "password": "Sifre!234",
        "full_name": f"Test Kullanıcı {index}",
    }


def login_payload(index: int = 1) -> Dict[str, str]:
    return {"email": f"user{index}@example.com", "password": "Sifre!234"}


def prediction_payload(symbol: str = "BTCUSDT") -> Dict[str, object]:
    return {"symbol": symbol, "horizon_days": 30, "risk_level": "medium"}


def exp_pair(seconds: int = 1) -> tuple[datetime, datetime]:
    now = datetime.utcnow()
    return now, now + timedelta(seconds=seconds)
