"""Parse human-friendly durations like '90s' or '1h30m' into seconds."""
import re

UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
_TOKEN = re.compile(r"(\d+)([dhms])")


def parse_duration(s):
    s = s.strip()
    if not s:
        raise ValueError("empty duration")
    total = 0
    pos = 0
    for m in _TOKEN.finditer(s):
        if m.start() != pos:
            break
        total += int(m.group(1)) * UNITS[m.group(2)]
        pos = m.end()
    if pos != len(s):
        raise ValueError(f"invalid duration: {s!r}")
    return total
