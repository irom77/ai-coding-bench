import json

from appconfig.merge import merge

DEFAULTS = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "options": {"timeout": 30, "ssl": False},
    },
    "features": ["search"],
    "debug": False,
}


def load(overrides=None, defaults=None):
    defaults = DEFAULTS if defaults is None else defaults
    return merge(defaults, overrides or {})


def load_file(path, defaults=None):
    with open(path) as f:
        return load(json.load(f), defaults)
