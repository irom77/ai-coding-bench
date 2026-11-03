import os


def delete_files(paths, out):
    for path in paths:
        os.remove(path)
        print(f"deleted: {path}", file=out)
    print(f"deleted {len(paths)} files", file=out)
    return len(paths)
