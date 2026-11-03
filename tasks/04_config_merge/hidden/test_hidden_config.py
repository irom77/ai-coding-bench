import copy
import json

from appconfig import DEFAULTS, load, load_file
from appconfig.merge import merge

PRISTINE = copy.deepcopy(DEFAULTS)


def test_three_levels_deep():
    cfg = load({"database": {"options": {"timeout": 5}}})
    assert cfg["database"]["options"] == {"timeout": 5, "ssl": False}
    assert cfg["database"]["host"] == "localhost"


def test_lists_replace():
    assert load({"features": ["billing"]})["features"] == ["billing"]


def test_none_replaces():
    assert load({"database": {"host": None}})["database"]["host"] is None


def test_scalar_replaces_dict_and_dict_replaces_scalar():
    assert merge({"a": {"b": 1}}, {"a": 3}) == {"a": 3}
    assert merge({"a": 3}, {"a": {"b": 1}}) == {"a": {"b": 1}}


def test_new_keys_added():
    assert load({"cache": {"ttl": 60}})["cache"] == {"ttl": 60}


def test_repeated_loads_are_stable():
    load({"debug": True, "database": {"port": 1}})
    assert load() == PRISTINE
    assert DEFAULTS == PRISTINE


def test_inputs_not_mutated():
    base = {"a": {"b": 1, "c": 2}}
    override = {"a": {"b": 9}, "d": [1]}
    base_copy, override_copy = copy.deepcopy(base), copy.deepcopy(override)
    merge(base, override)
    assert base == base_copy
    assert override == override_copy


def test_result_shares_nothing():
    override = {"features": ["x"], "extra": {"k": 1}}
    cfg = load(override)
    cfg["database"]["options"]["ssl"] = True
    cfg["features"].append("y")
    cfg["extra"]["k"] = 2
    assert DEFAULTS == PRISTINE
    assert override == {"features": ["x"], "extra": {"k": 1}}
    assert load() == PRISTINE


def test_load_file(tmp_path):
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps({"database": {"port": 7000}}))
    cfg = load_file(p)
    assert cfg["database"] == {"host": "localhost", "port": 7000, "options": {"timeout": 30, "ssl": False}}
