import time
from enum import Enum
from typing import NamedTuple


class ThrottleResult(str, Enum):
    ALLOWED = "allowed"
    IP_LIMITED = "ip_limited"
    ACCOUNT_COOLDOWN = "account_cooldown"


class ThrottleResponse(NamedTuple):
    status: ThrottleResult
    retry_after_seconds: int = 0


class AuthThrottle:
    """
    In-memory and database-backed rate limiter for authentication endpoints:
    - IP Rate Limiting: 30 requests per minute per IP.
    - Account Failure Limiting: 5 failed attempts in 10 minutes triggers 60s cooldown.
    """

    def __init__(self, ip_limit: int = 30, failure_limit: int = 5, cooldown_seconds: int = 60):
        self.ip_limit = ip_limit
        self.failure_limit = failure_limit
        self.cooldown_seconds = cooldown_seconds

        # IP tracking: ip -> list of timestamps
        self.ip_requests: dict[str, list[float]] = {}
        # Account failure tracking: email -> list of failure timestamps
        self.account_failures: dict[str, list[float]] = {}
        # Cooldown tracking: email -> cooldown_until_timestamp
        self.account_cooldowns: dict[str, float] = {}

    def record_attempt(self, ip: str, email: str, success: bool) -> ThrottleResponse:
        now = time.time()
        email_clean = email.strip().lower()

        # 1. Check IP rate limit (last 60s)
        ip_history = self.ip_requests.setdefault(ip, [])
        ip_history = [t for t in ip_history if now - t < 60.0]
        self.ip_requests[ip] = ip_history

        if len(ip_history) >= self.ip_limit:
            return ThrottleResponse(status=ThrottleResult.IP_LIMITED, retry_after_seconds=60)

        ip_history.append(now)

        # 2. Check Account Cooldown
        cooldown_until = self.account_cooldowns.get(email_clean, 0.0)
        if now < cooldown_until:
            rem = int(cooldown_until - now) + 1
            return ThrottleResponse(status=ThrottleResult.ACCOUNT_COOLDOWN, retry_after_seconds=rem)

        if success:
            # Successful login clears failure counter
            self.account_failures.pop(email_clean, None)
            self.account_cooldowns.pop(email_clean, None)
            return ThrottleResponse(status=ThrottleResult.ALLOWED, retry_after_seconds=0)

        # Record failure
        failures = self.account_failures.setdefault(email_clean, [])
        failures = [t for t in failures if now - t < 600.0]  # 10 minutes window
        failures.append(now)
        self.account_failures[email_clean] = failures

        if len(failures) >= self.failure_limit:
            # Trigger cooldown
            self.account_cooldowns[email_clean] = now + self.cooldown_seconds
            # Reset failure history for fresh window after cooldown
            self.account_failures[email_clean] = []
            return ThrottleResponse(
                status=ThrottleResult.ACCOUNT_COOLDOWN,
                retry_after_seconds=self.cooldown_seconds,
            )

        return ThrottleResponse(status=ThrottleResult.ALLOWED, retry_after_seconds=0)
