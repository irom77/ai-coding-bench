"""Token-bucket rate limiter.

Specification
-------------
TokenBucket(capacity, rate, clock=time.monotonic)
    capacity: maximum number of tokens; must be > 0, else ValueError.
    rate:     tokens added per second; must be >= 0, else ValueError.
    clock:    zero-argument callable returning the current time in seconds.

    The bucket starts full. Tokens refill continuously (fractional tokens are
    allowed) based on elapsed clock time, and never exceed capacity.

allow(n=1) -> bool
    If at least n tokens are available, consume n and return True.
    Otherwise consume nothing and return False.
    n must satisfy 1 <= n <= capacity, else ValueError.

available() -> float
    Current number of tokens (after applying any refill), without consuming.
"""
import time


class TokenBucket:
    def __init__(self, capacity, rate, clock=time.monotonic):
        raise NotImplementedError

    def allow(self, n=1):
        raise NotImplementedError

    def available(self):
        raise NotImplementedError
