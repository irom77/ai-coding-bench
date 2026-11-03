#!/usr/bin/env bash
# Sanity-check the kit itself before benchmarking real models.
#   oracle  -> applies reference solutions, must pass 6/6
#   noop    -> does nothing, must fail 6/6
#   cheater -> deletes the tests, must be flagged TAMPERED and fail
#   manual  -> manual mode with scripted keypresses (1 continue, then done; last task gave up):
#              must fail 6/6, cont=1, gave=1
set -euo pipefail
cd "$(dirname "$0")"
OUT=results/selftest.jsonl
rm -f "$OUT"
python3 run.py --name oracle  --agent 'python3 '"$PWD"'/agents/oracle.py' --runs 1 --results "$OUT"
python3 run.py --name noop    --agent 'true'                              --runs 1 --results "$OUT"
python3 run.py --name cheater --agent 'rm -rf tests'                      --runs 1 --results "$OUT"
NTASKS=$(ls -d tasks/*/ | wc -l)
{ for _ in $(seq $((NTASKS - 1))); do printf 'c\n\n'; done; printf 'c\ng\n'; } |
  python3 run.py --name manual --manual --no-open --note selftest --runs 1 --results "$OUT" >/dev/null
python3 report.py --results "$OUT"
