from pager import paginate, total_pages


def test_second_page():
    assert paginate(list(range(25)), 2, 10) == list(range(10, 20))


def test_total_pages_exact():
    assert total_pages(20, 10) == 2
