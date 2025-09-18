from typing import List, Optional, Tuple


def sma(prices: List[float], n: int) -> Optional[float]:
    if len(prices) < n:
        return None
    return sum(prices[-n:]) / n


def ema(prices: List[float], n: int) -> Optional[float]:
    if len(prices) < n:
        return None
    k = 2 / (n + 1)
    e = prices[0]
    for p in prices[1:]:
        e = p * k + e * (1 - k)
    return e


def rsi(prices: List[float], period: int = 14) -> Optional[float]:
    if len(prices) <= period:
        return None
    gains, losses = [], []
    for i in range(1, len(prices)):
        ch = prices[i] - prices[i - 1]
        gains.append(max(ch, 0.0))
        losses.append(abs(min(ch, 0.0)))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rsis = []
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = avg_gain / (avg_loss if avg_loss != 0 else 1e-9)
        rsis.append(100 - (100 / (1 + rs)))
    return rsis[-1] if rsis else None


def macd(prices: List[float], fast=12, slow=26, signal=9) -> Optional[Tuple[float, float]]:
    if len(prices) < slow + signal:
        return None

    def _ema(seq, n):
        k = 2 / (n + 1)
        e = seq[0]
        for p in seq[1:]:
            e = p * k + e * (1 - k)
        return e

    macd_val = _ema(prices, fast) - _ema(prices, slow)
    # signal için basit yaklaşım: rolling EMA'ların EMA'sı
    series = []
    for i in range(len(prices)):
        sub = prices[: i + 1]
        series.append(_ema(sub, fast) - _ema(sub, slow))
    signal_val = _ema(series, signal)
    return macd_val, signal_val
