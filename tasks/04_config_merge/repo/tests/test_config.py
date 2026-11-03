from appconfig import load


def test_top_level_override():
    assert load({"debug": True})["debug"] is True


def test_partial_nested_override():
    cfg = load({"database": {"port": 6543}})
    assert cfg["database"]["port"] == 6543
    assert cfg["database"]["host"] == "localhost"
