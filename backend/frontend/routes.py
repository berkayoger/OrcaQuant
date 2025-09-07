from flask import render_template

from . import frontend_bp


@frontend_bp.route("/")
def index():
    return render_template("index.html")


@frontend_bp.route("/predictions")
def prediction_display():
    """Render the public predictions page."""
    return render_template("prediction_display.html")


@frontend_bp.route("/websocket-demo")
def websocket_demo():
    """WebSocket demo page for testing real-time price updates."""
    return render_template("websocket_demo.html")
