import argparse
import sys

from cleaner.actions import delete_files
from cleaner.finder import find_matches


def build_parser():
    p = argparse.ArgumentParser(prog="cleaner", description="Delete files matching a pattern.")
    p.add_argument("root", help="directory to scan")
    p.add_argument("--pattern", default="*.tmp", help="glob for file names (default: *.tmp)")
    p.add_argument("--older-than", type=float, default=None, metavar="DAYS",
                   help="only files last modified at least DAYS ago")
    return p


def main(argv=None, out=None):
    out = out or sys.stdout
    args = build_parser().parse_args(argv)
    paths = find_matches(args.root, args.pattern, args.older_than)
    delete_files(paths, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
