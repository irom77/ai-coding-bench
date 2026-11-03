import io
import os
import time

from cleaner.cli import main


def _tree(tmp_path):
    (tmp_path / "sub").mkdir()
    files = [tmp_path / "b.tmp", tmp_path / "a.tmp", tmp_path / "sub" / "c.tmp", tmp_path / "keep.log"]
    for f in files:
        f.write_text("x")
    return files


def test_dry_run_deletes_nothing_and_reports(tmp_path):
    files = _tree(tmp_path)
    out = io.StringIO()
    assert main([str(tmp_path), "--dry-run"], out=out) == 0
    assert all(f.exists() for f in files)
    expected = sorted(str(f) for f in files if f.suffix == ".tmp")
    assert out.getvalue().splitlines() == [f"would delete: {p}" for p in expected] + ["would delete 3 files"]


def test_dry_run_with_pattern(tmp_path):
    _tree(tmp_path)
    out = io.StringIO()
    assert main([str(tmp_path), "--pattern", "*.log", "--dry-run"], out=out) == 0
    assert out.getvalue().splitlines() == [f"would delete: {tmp_path / 'keep.log'}", "would delete 1 files"]
    assert (tmp_path / "keep.log").exists()


def test_dry_run_flag_position_and_older_than(tmp_path):
    old, new = tmp_path / "old.tmp", tmp_path / "new.tmp"
    old.write_text("x")
    new.write_text("x")
    ten_days_ago = time.time() - 10 * 86400
    os.utime(old, (ten_days_ago, ten_days_ago))
    out = io.StringIO()
    assert main(["--dry-run", "--older-than", "5", str(tmp_path)], out=out) == 0
    assert out.getvalue().splitlines() == [f"would delete: {old}", "would delete 1 files"]
    assert old.exists() and new.exists()


def test_dry_run_no_matches(tmp_path):
    out = io.StringIO()
    assert main([str(tmp_path), "--dry-run"], out=out) == 0
    assert out.getvalue().splitlines() == ["would delete 0 files"]


def test_normal_mode_unchanged(tmp_path):
    files = _tree(tmp_path)
    out = io.StringIO()
    assert main([str(tmp_path)], out=out) == 0
    expected = sorted(str(f) for f in files if f.suffix == ".tmp")
    assert out.getvalue().splitlines() == [f"deleted: {p}" for p in expected] + ["deleted 3 files"]
    assert not any(os.path.exists(p) for p in expected)
    assert (tmp_path / "keep.log").exists()
