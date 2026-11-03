"""Simple list pagination helpers."""


def total_pages(n_items, per_page):
    """Number of pages needed to show n_items, per_page at a time."""
    return n_items // per_page


def paginate(items, page, per_page=10):
    """Return the items on a 1-indexed page."""
    start = page * per_page
    return items[start:start + per_page]
