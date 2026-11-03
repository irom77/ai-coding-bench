"""Parse human-friendly durations like '90s' or '5m' into seconds."""

UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_duration(s):
    s = s.strip()
    num = ""
    for i, ch in enumerate(s):
        if ch.isdigit():
            num += ch
        else:
            unit = s[i:]
            if unit not in UNITS:
                raise ValueError(f"invalid unit: {unit}")
            return int(num) * UNITS[unit]
    raise ValueError("missing unit")
