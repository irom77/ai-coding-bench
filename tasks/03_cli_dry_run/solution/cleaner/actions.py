import os


def delete_files(paths, out, dry_run=False):
    verb = "would delete" if dry_run else "deleted"
    for path in paths:
        if not dry_run:
            os.remove(path)
        print(f"{verb}: {path}", file=out)
    print(f"{verb} {len(paths)} files", file=out)
    return len(paths)
