import math
import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request


class RateLimiter:
    """
    In-memory protections for scan creation requests.

    1. Per-domain cooldown: 60s between scans of the same domain.
    2. Per-IP rate limit: 10 scan requests per rolling 60s window.

    The state is protected by a lock because FastAPI can handle
    multiple requests concurrently within the same process.
    """

    def __init__(
        self,
        domain_cooldown_seconds: int = 60,
        ip_max_requests: int = 10,
        ip_window_seconds: int = 60,
    ):
        self.domain_cooldowns: dict[str, float] = {}
        self.ip_requests: dict[str, list[float]] = defaultdict(list)
        self.domain_cooldown_seconds = domain_cooldown_seconds
        self.ip_max_requests = ip_max_requests
        self.ip_window_seconds = ip_window_seconds
        self._lock = Lock()

    def _get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def check_domain_cooldown(self, domain: str) -> None:
        now = time.time()

        with self._lock:
            last_scan = self.domain_cooldowns.get(domain)
            if last_scan is not None:
                remaining = self.domain_cooldown_seconds - (now - last_scan)
                if remaining > 0:
                    retry_after = max(1, math.ceil(remaining))
                    raise HTTPException(
                        status_code=429,
                        detail=(
                            f"'{domain}' was scanned recently. "
                            f"Please wait {retry_after} seconds before rescanning."
                        ),
                        headers={"Retry-After": str(retry_after)},
                    )

            self.domain_cooldowns[domain] = now

    def check_ip_rate_limit(self, request: Request) -> None:
        client_ip = self._get_client_ip(request)
        now = time.time()
        window_start = now - self.ip_window_seconds

        with self._lock:
            recent_requests = [
                timestamp
                for timestamp in self.ip_requests[client_ip]
                if timestamp > window_start
            ]

            if len(recent_requests) >= self.ip_max_requests:
                oldest_request = min(recent_requests)
                retry_after = max(
                    1,
                    math.ceil((oldest_request + self.ip_window_seconds) - now),
                )
                raise HTTPException(
                    status_code=429,
                    detail=(
                        f"Too many scan requests from this IP. "
                        f"Maximum {self.ip_max_requests} requests per "
                        f"{self.ip_window_seconds} seconds."
                    ),
                    headers={"Retry-After": str(retry_after)},
                )

            recent_requests.append(now)
            self.ip_requests[client_ip] = recent_requests

    def enforce_scan_limits(self, request: Request, domain: str) -> None:
        self.check_ip_rate_limit(request)
        self.check_domain_cooldown(domain)

    def get_domain_cooldown_status(self, domain: str) -> dict:
        with self._lock:
            last_scan = self.domain_cooldowns.get(domain)

        if last_scan is None:
            return {"on_cooldown": False, "remaining_seconds": 0}

        remaining = max(0, self.domain_cooldown_seconds - (time.time() - last_scan))
        return {
            "on_cooldown": remaining > 0,
            "remaining_seconds": math.ceil(remaining),
        }

    def reset(self) -> None:
        with self._lock:
            self.domain_cooldowns.clear()
            self.ip_requests.clear()


limiter = RateLimiter(
    domain_cooldown_seconds=60,
    ip_max_requests=10,
    ip_window_seconds=60,
)
