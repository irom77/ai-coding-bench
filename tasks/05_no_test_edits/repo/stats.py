"""Tiny statistics helpers."""


def mean(xs):
    return sum(xs) / len(xs)


def median(xs):
    n = len(xs)
    return xs[n // 2]
