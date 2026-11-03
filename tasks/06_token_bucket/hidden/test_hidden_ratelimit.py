import pytest

from ratelimit import TokenBucket


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def test_refills_over_time():
    clock = FakeClock()
    b = TokenBucket(2, 1, clock=clock)
    assert b.allow() and b.allow() and not b.allow()
    clock.t += 1
    assert b.allow()
    assert not b.allow()


def test_never_exceeds_capacity():
    clock = FakeClock()
    b = TokenBucket(2, 10, clock=clock)
    clock.t += 100
    assert b.available() == pytest.approx(2)


def test_fractional_refill():
    clock = FakeClock()
    b = TokenBucket(1, 2, clock=clock)
    assert b.allow()
    clock.t += 0.25
    assert b.available() == pytest.approx(0.5)
    assert not b.allow()
    clock.t += 0.25
    assert b.allow()


def test_allow_n_and_failed_allow_consumes_nothing():
    clock = FakeClock()
    b = TokenBucket(5, 1, clock=clock)
    assert b.allow(3)
    assert not b.allow(3)
    assert b.available() == pytest.approx(2)
    assert b.allow(2)


def test_zero_rate_never_refills():
    clock = FakeClock()
    b = TokenBucket(1, 0, clock=clock)
    assert b.allow()
    clock.t += 1e6
    assert not b.allow()


@pytest.mark.parametrize("n", [0, -1, 6])
def test_invalid_n(n):
    with pytest.raises(ValueError):
        TokenBucket(5, 1, clock=FakeClock()).allow(n)


@pytest.mark.parametrize("capacity,rate", [(0, 1), (-1, 1), (1, -0.5)])
def test_invalid_constructor(capacity, rate):
    with pytest.raises(ValueError):
        TokenBucket(capacity, rate, clock=FakeClock())


def test_default_clock_works():
    b = TokenBucket(1, 1)
    assert b.allow()
    assert 0 <= b.available() < 1
