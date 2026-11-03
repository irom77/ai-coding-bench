import io

from cleaner.cli import main


def test_deletes_matching_files(tmp_path):
    (tmp_path / "a.tmp").write_text("x")
    (tmp_path / "keep.txt").write_text("x")
    out = io.StringIO()
    assert main([str(tmp_path)], out=out) == 0
    assert not (tmp_path / "a.tmp").exists()
    assert (tmp_path / "keep.txt").exists()
    assert out.getvalue().splitlines() == [f"deleted: {tmp_path / 'a.tmp'}", "deleted 1 files"]
