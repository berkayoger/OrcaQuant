from __future__ import annotations
from celery import shared_task
from backend.ml.train import train as ml_train


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def train_model_task(self, symbol: str = "BTC/USDT", horizon: int = 7):
    return ml_train(symbol=symbol, horizon=horizon)

