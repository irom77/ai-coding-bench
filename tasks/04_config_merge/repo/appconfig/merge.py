def merge(base, override):
    """Merge override into base and return the result."""
    result = base
    result.update(override)
    return result
