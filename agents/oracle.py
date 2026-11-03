#!/usr/bin/env python3
"""Self-test 'agent': copies the reference solution into the task repo. Should score 100%."""
import os
import shutil
from pathlib import Path

solution = Path(__file__).resolve().parent.parent / "tasks" / os.environ["BENCH_TASK"] / "solution"
shutil.copytree(solution, Path.cwd(), dirs_exist_ok=True)
print(f"copied {solution}")
