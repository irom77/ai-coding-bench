import pytest

from stats import mean, median


@pytest.mark.parametrize("data,expected", [
    ([7], 7),
    ([-5, 10, 0], 0),
    ([10, 2, 38, 23, 38, 23, 21], 23),
    ([1.5, 0.5], 1.0),
    ((9, 1, 5), 5),
])
def test_median_cases(data, expected):
    assert median(data) == expected


def test_mean_single():
    assert mean([5]) == 5


def test_mean_tuple():
    assert mean((1, 2)) == 1.5
