from durations import parse_duration


def test_seconds():
    assert parse_duration("90s") == 90


def test_minutes():
    assert parse_duration("5m") == 300


def test_combined():
    assert parse_duration("1h30m") == 5400
