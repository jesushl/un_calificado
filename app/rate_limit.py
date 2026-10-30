import time
from collections import defaultdict, deque
from threading import Lock

from flask import request

from .errors import ApiError

_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def enforce_rate_limit(scope: str, limit: int = 10, window_seconds: int = 60) -> None:
    identity = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
    key = f"{scope}:{identity.split(',')[0].strip()}"
    now = time.monotonic()
    with _lock:
        bucket = _hits[key]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            raise ApiError(
                429,
                "RATE_LIMITED",
                "Demasiados intentos. Espera un momento e inténtalo de nuevo.",
            )
        bucket.append(now)
