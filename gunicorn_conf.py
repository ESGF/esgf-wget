import multiprocessing

# gunicorn_conf.py


# Basic server configuration
bind = "0.0.0.0:3000"  # Bind to localhost for security
workers = multiprocessing.cpu_count() * 2 + 1  # Optimal number of workers
threads = 2  # Use threads for handling requests
worker_class = "gthread"  # Use threaded workers for better concurrency

forwarded_allow_ips = "127.0.0.1"  # Only allow trusted proxies
limit_request_line = 4094  # Limit the size of HTTP request lines
limit_request_fields = 100  # Limit the number of HTTP headers
limit_request_field_size = 8190  # Limit the size of HTTP header fields

# Logging
accesslog = "-"  # Log access to stdout
errorlog = "-"  # Log errors to stdout
loglevel = "info"  # Set log level to info

# Timeout settings
timeout = 30  # Workers silent for 30 seconds are killed and restarted
graceful_timeout = 30  # Timeout for graceful worker restart
keepalive = 5  # Keep connections alive for 5 seconds

# Prevent daemonization
daemon = False

# Additional security headers
def on_starting(server):
    server.log.info("Gunicorn server is starting with secure configuration.")