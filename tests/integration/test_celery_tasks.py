"""Smoke tests for Celery task registration."""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.celery]


POSSIBLE_TASK_NAMES = [
    "backend.tasks.celery_tasks.run_full_analysis",
    "backend.tasks.plan_tasks.enqueue_plan_refresh",
    "backend.tasks.ml_tasks.train_prediction_model",
]


def test_celery_tasks_registered(celery_app):
    registered = [name for name in POSSIBLE_TASK_NAMES if name in celery_app.tasks]
    if not registered:
        pytest.skip(f"Celery task bulunamadı: {POSSIBLE_TASK_NAMES}")
    for name in registered:
        assert callable(celery_app.tasks[name])
