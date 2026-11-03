"""Tiny statistics helpers."""


def mean(xs):
    if not xs:
        raise ValueError("mean() of empty data")
    return sum(xs) / len(xs)


def median(xs):
    if not xs:
        raise ValueError("median() of empty data")
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2
