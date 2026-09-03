from collections import defaultdict
from time import time

from fastapi import HTTPException, Request, status

_PURGE_THRESHOLD = 1000


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


class RateLimiter:
    def __init__(self, window_seconds: int, max_attempts: int):
        self.window_seconds = window_seconds
        self.max_attempts = max_attempts
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, detail: str) -> None:
        now = time()
        attempts = self._attempts[key]
        attempts[:] = [timestamp for timestamp in attempts if now - timestamp < self.window_seconds]
        if len(attempts) >= self.max_attempts:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)
        attempts.append(now)

        if len(self._attempts) > _PURGE_THRESHOLD:
            self._purge_expired(now)

    def _purge_expired(self, now: float) -> None:
        expired_keys = [
            key
            for key, timestamps in self._attempts.items()
            if not timestamps or now - timestamps[-1] >= self.window_seconds
        ]
        for expired_key in expired_keys:
            del self._attempts[expired_key]
