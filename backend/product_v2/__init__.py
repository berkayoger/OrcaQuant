"""
OrcaQuant product v2 bootstrap (non-invasive).
Yalnızca v2 namespace'i altında blueprint'leri kaydeder.
"""
from typing import Optional


def init_app(app, prefix: Optional[str] = "/api/v2"):
    if getattr(app, "_oq_product_v2_attached", False):
        return app
    # Indicators v2
    from .blueprints.indicators import bp as indicators_bp
    app.register_blueprint(indicators_bp, url_prefix=f"{prefix}/indicators")
    # market v2
    from .blueprints.market import bp as market_bp
    app.register_blueprint(market_bp, url_prefix=f"{prefix}/market")
    # portfolio v2
    from .blueprints.portfolio import bp as portfolio_bp
    app.register_blueprint(portfolio_bp, url_prefix=f"{prefix}/portfolio")
    # alerts v2
    from .blueprints.alerts import bp as alerts_bp
    app.register_blueprint(alerts_bp, url_prefix=f"{prefix}/alerts")
    app._oq_product_v2_attached = True
    return app
