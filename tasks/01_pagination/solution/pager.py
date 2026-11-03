"""Simple list pagination helpers."""


def _check_per_page(per_page):
    if per_page < 1:
        raise ValueError("per_page must be >= 1")


def total_pages(n_items, per_page):
    """Number of pages needed to show n_items, per_page at a time."""
    _check_per_page(per_page)
    return -(-n_items // per_page)


def paginate(items, page, per_page=10):
    """Return the items on a 1-indexed page."""
    _check_per_page(per_page)
    if page < 1:
        raise ValueError("page must be >= 1")
    start = (page - 1) * per_page
    return items[start:start + per_page]
