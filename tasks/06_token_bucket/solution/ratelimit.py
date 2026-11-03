"""Token-bucket rate limiter (reference solution)."""
import time


class TokenBucket:
    def __init__(self, capacity, rate, clock=time.monotonic):
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        if rate < 0:
            raise ValueError("rate must be >= 0")
        self.capacity = capacity
        self.rate = rate
        self._clock = clock
        self._tokens = float(capacity)
        self._last = clock()

    def _refill(self):
        now = self._clock()
        elapsed = max(0.0, now - self._last)
        self._last = now
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)

    def allow(self, n=1):
        if not 1 <= n <= self.capacity:
            raise ValueError("n must be between 1 and capacity")
        self._refill()
        if self._tokens >= n:
            self._tokens -= n
            return True
        return False

    def available(self):
        self._refill()
        return self._tokens
