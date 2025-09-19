"""Load repository-level pytest fixtures within backend test package."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("_root_conftest", ROOT / "conftest.py")
if spec and spec.loader:  # pragma: no cover - defensive
    root_conftest = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(root_conftest)
    globals().update({k: v for k, v in vars(root_conftest).items() if not k.startswith("__")})
