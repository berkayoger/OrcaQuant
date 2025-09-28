"""Production-focused Gunicorn configuration for OrcaQuant."""

import multiprocessing
import os

#
# Nginx terminates TLS and proxies internally to localhost:5000
#
bind = "127.0.0.1:5000"

# Workers: (2 * CPU) + 1 by default; can be overridden via env
workers = int(os.getenv("GUNICORN_WORKERS", (multiprocessing.cpu_count() * 2) + 1))
threads = int(os.getenv("GUNICORN_THREADS", 2))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")  # For Socket.IO full WS, consider gevent*

# Timeouts tuned for API workloads (seconds)
timeout = int(os.getenv("GUNICORN_TIMEOUT", 60))
graceful_timeout = 30
keepalive = 5

# Request/headers size limits to mitigate abuse
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

worker_tmp_dir = "/tmp"

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")
