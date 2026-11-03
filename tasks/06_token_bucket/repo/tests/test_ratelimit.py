from ratelimit import TokenBucket


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def test_starts_full_then_denies():
    bucket = TokenBucket(3, 1, clock=FakeClock())
    assert [bucket.allow() for _ in range(4)] == [True, True, True, False]
