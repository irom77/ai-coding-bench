import pytest

from stats import mean, median


def test_mean():
    assert mean([1, 2, 3, 4]) == 2.5


def test_mean_empty_raises_value_error():
    with pytest.raises(ValueError):
        mean([])


def test_median_unsorted():
    assert median([3, 1, 2]) == 2


def test_median_even_length():
    assert median([4, 1, 3, 2]) == 2.5


def test_median_empty_raises_value_error():
    with pytest.raises(ValueError):
        median([])


def test_median_does_not_mutate_input():
    data = [3, 1, 2]
    median(data)
    assert data == [3, 1, 2]
