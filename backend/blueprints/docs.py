"""Blueprint serving API documentation (OpenAPI + ReDoc)."""
from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template_string

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

bp = Blueprint("docs", __name__)

_REDOC_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>OrcaQuant API Docs</title>
    <link rel="preconnect" href="https://cdn.jsdelivr.net" />
  </head>
  <body>
    <redoc spec-url="/api/openapi.json"></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js"></script>
  </body>
</html>
"""


@bp.get("/api/openapi.json")
def openapi_json():
    spec_path = Path(current_app.root_path).parent / "docs" / "openapi.yaml"
    with spec_path.open("r", encoding="utf-8") as handle:
        if yaml is None:
            return jsonify({"error": "missing_dependency", "detail": "PyYAML is required"}), 500
        data = yaml.safe_load(handle)
    return jsonify(data)


@bp.get("/api/docs")
def docs_index():
    return render_template_string(_REDOC_HTML)
