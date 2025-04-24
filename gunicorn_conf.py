import os
import multiprocessing

bind = "0.0.0.0:3000"
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2 
worker_class = "gthread"

forwarded_allow_ips = os.environ.get("GUNICORN_TRUSTED_PROXIES", "127.0.0.1")
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

accesslog = "-"  # Log access to stdout
errorlog = "-"  # Log errors to stdout
loglevel = "info"  # Set log level to info

timeout = 30  # Workers silent for 30 seconds are killed and restarted
graceful_timeout = 30  # Timeout for graceful worker restart
keepalive = 5  # Keep connections alive for 5 seconds

daemon = False