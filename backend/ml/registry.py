from __future__ import annotations
import os
import json
from typing import Optional, Dict, Any

try:
    import mlflow  # type: ignore
except Exception:
    mlflow = None

ARTIFACT_DIR = os.environ.get("ML_ARTIFACT_DIR", "storage/models")
os.makedirs(ARTIFACT_DIR, exist_ok=True)
REG_FILE = os.path.join(ARTIFACT_DIR, "registry.json")

def _read_registry() -> Dict[str, Any]:
    if os.path.exists(REG_FILE):
        try:
            with open(REG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _write_registry(data: Dict[str, Any]) -> None:
    with open(REG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def register_model_local(name: str, version: str, path: str, metrics: dict) -> None:
    reg = _read_registry()
    reg.setdefault(name, {})[version] = {"path": path, "metrics": metrics}
    reg[name]["latest"] = version
    _write_registry(reg)

def get_model_path(name: str, version: Optional[str] = None) -> Optional[str]:
    reg = _read_registry()
    if name not in reg:
        return None
    if version is None:
        version = reg[name].get("latest")
    item = reg[name].get(version) if version else None
    if item:
        return item.get("path")
    return None

def use_mlflow() -> bool:
    return mlflow is not None and bool(os.environ.get("MLFLOW_TRACKING_URI"))

