import pytest

from durations import parse_duration


@pytest.mark.parametrize("text,expected", [
    ("45s", 45),
    ("2h", 7200),
    ("3d", 259200),
    ("2d4h", 187200),
    ("1h30m15s", 5415),
    ("  5m ", 300),
    ("0s", 0),
])
def test_valid(text, expected):
    result = parse_duration(text)
    assert result == expected
    assert isinstance(result, int)


@pytest.mark.parametrize("text", ["", "   ", "5x", "h", "10", "1h30", "m5", "1h-5m", "1.5h"])
def test_invalid(text):
    with pytest.raises(ValueError):
        parse_duration(text)
