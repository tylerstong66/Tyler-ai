"""Gunicorn settings for synchronous provider-backed training requests."""

# A champion-training command performs several bounded model calls before it can
# return one atomic response. The default 30-second worker limit can terminate a
# healthy request mid-benchmark and leave the browser with an empty HTTP 500.
timeout = 120
graceful_timeout = 30
keepalive = 5
