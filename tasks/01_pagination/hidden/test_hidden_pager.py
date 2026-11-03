import pytest

from pager import paginate, total_pages


def test_first_page():
    assert paginate(list(range(25)), 1, 10) == list(range(10))


def test_last_partial_page():
    assert paginate(list(range(25)), 3, 10) == [20, 21, 22, 23, 24]


def test_past_end_is_empty():
    assert paginate(list(range(25)), 4, 10) == []


def test_total_pages_partial():
    assert total_pages(25, 10) == 3


def test_total_pages_zero_items():
    assert total_pages(0, 10) == 0


@pytest.mark.parametrize("page", [0, -1])
def test_invalid_page(page):
    with pytest.raises(ValueError):
        paginate([1, 2, 3], page, 2)


@pytest.mark.parametrize("per_page", [0, -5])
def test_invalid_per_page(per_page):
    with pytest.raises(ValueError):
        total_pages(5, per_page)
    with pytest.raises(ValueError):
        paginate([1, 2, 3], 1, per_page)
