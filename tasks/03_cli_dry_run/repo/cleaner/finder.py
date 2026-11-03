import fnmatch
import os
import time


def find_matches(root, pattern, older_than_days=None, now=None):
    """Return sorted paths under root whose file name matches pattern."""
    now = time.time() if now is None else now
    matches = []
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if not fnmatch.fnmatch(name, pattern):
                continue
            path = os.path.join(dirpath, name)
            if older_than_days is not None:
                age_days = (now - os.path.getmtime(path)) / 86400
                if age_days < older_than_days:
                    continue
            matches.append(path)
    return sorted(matches)
