#!/usr/bin/env python3
"""
OrcaQuant with Socket.IO support
Production'da gunicorn + eventlet kullanın
"""
import os
import logging
from backend import create_app

# Create Flask app
app = create_app()

if __name__ == "__main__":
    # Development server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    
    logging.basicConfig(level=logging.INFO)
    
    # Use socketio.run instead of app.run
    app.socketio.run(
        app, 
        host=host, 
        port=port, 
        debug=debug,
        allow_unsafe_werkzeug=True
    )
