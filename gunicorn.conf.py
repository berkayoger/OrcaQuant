"""Production-focused Gunicorn configuration."""

import multiprocessing
import os

# Bind to localhost; Nginx terminates TLS and proxies requests internally.
bind = "127.0.0.1:5000"

# Formula recommended by the Gunicorn docs. Allow overrides via env vars.
workers = int(os.getenv("GUNICORN_WORKERS", (multiprocessing.cpu_count() * 2) + 1))
threads = int(os.getenv("GUNICORN_THREADS", 2))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")

timeout = int(os.getenv("GUNICORN_TIMEOUT", 60))
graceful_timeout = 30
keepalive = 5

# Header/line limits mitigate abuse from extremely large requests.
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

worker_tmp_dir = "/tmp"

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")
