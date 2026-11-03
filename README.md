# ai-coding-bench

A small, honest benchmark for comparing AI coding assistants on the same tasks under the same conditions.
It works with any agent you can run from a shell command. Requires Python 3.9+ and git. If your Python has no pytest, the runner installs it once into `.venv/` inside the kit.

## How it works

For every task and repeat, the runner:

1. copies the task's starter repo into a fresh temp dir (outside this kit, so the agent can't see hidden tests) and makes a baseline git commit;
2. runs your agent command inside it with the task prompt;
3. checks whether protected files (the visible tests) were tampered with: deleted, lines removed or changed, or skip/xfail added. Purely *adding* tests is allowed and only reported (`tests_added_to`);
4. grades with **hidden tests** plus a pristine copy of the visible tests. Agent-written `conftest.py` and `pytest.ini` files are ignored, and skipped tests count as failures;
5. records pass/fail, partial score, time, diff size and tampering to `results/results.jsonl`.

A run **passes** only if every hidden test passes and no protected file was tampered with.

## Quick start

```bash
./selftest.sh          # sanity check: oracle 6/6, noop 0/6, cheater flagged, manual mode wiring

# Model A vs model B, 3 repeats each (18 runs per model)
python3 run.py --name model-a --agent 'claude -p {prompt} --model <model-a> --dangerously-skip-permissions'
python3 run.py --name model-b --agent 'claude -p {prompt} --model <model-b> --dangerously-skip-permissions'
python3 report.py
```

`--agent` is any shell command, run with the task repo as its working directory. Placeholders:

| placeholder     | value                                        |
|-----------------|----------------------------------------------|
| `{prompt}`      | the task prompt, shell-quoted                |
| `{prompt_file}` | path to a file containing the prompt         |
| `{workdir}`     | absolute path of the task repo               |

The env vars `BENCH_PROMPT` and `BENCH_TASK` are also set. Example command shapes for other CLIs (check the flags against your installed version):

```bash
--agent 'codex exec --full-auto {prompt}'
--agent 'aider --yes-always --no-auto-commits --model <model> --message {prompt}'
--agent 'my-agent run --prompt-file {prompt_file}'
```

Agents must run **non-interactively** (no permission prompts), or they will sit until `--timeout`.

**Speed and cost.** By default 6 runs go in parallel (`--jobs 6`) and each run is killed after 300 s (`--timeout 300`),
so a full 18-run benchmark usually takes a few minutes and in the worst case about 15. Use `--jobs 18` to run everything at once
(worst case ≈ one timeout) if your provider's rate limits allow it. The timeout also caps the cost of a runaway agent.
For a quick, cheap check use `--tasks 01 --runs 1`. Manual mode always runs one at a time.

Useful flags: `--tasks 01 03` (subset by prefix), `--runs 5`, `--jobs 6`, `--timeout 300`, `--workdir DIR`.
Report flags: `--agents a b`, `--run-id ...`, `--csv out.csv`, `--md` (regenerates `LEADERBOARD.md`, the table kept in the repo; rerun it after every new benchmark and commit it with `results/results.jsonl`).

## Manual / IDE agents

For agents you can't launch from a shell (IDE chat panels, internal VS Code extensions you type into):

```bash
python3 run.py --name copilot-chat --manual --runs 3
```

You're asked once to describe the agent (model, extension + version, settings), stored as `agent_note`.
Use `--note "..."` to skip the question. Then for every task and repeat, the runner prepares a fresh repo,
prints its path and the prompt (also saved to `PROMPT.txt`), opens the folder with `code` if that's on PATH
(`--no-open` to skip), and waits:

| key           | meaning                                                       |
|---------------|---------------------------------------------------------------|
| `c` + Enter   | you sent the agent "continue" (logged with a timestamp)       |
| Enter         | agent is done, so grade it                                    |
| `g` + Enter   | you gave up (still graded, marked `gave_up`)                  |

Grading and the tamper check are the same as for CLI agents, so `report.py` puts everyone in one table.
The `cont` column is the median number of continues per run and `gave` is the number of abandoned runs.

**Rules, to keep it honest:**
- Start a **fresh chat** for every run and paste the prompt exactly as given. Don't add context.
- The only follow-up allowed is **"continue"**, and you must log each one with `c`. No hints, no "you missed a case".
- Approving tool calls or edits the agent asks for is fine. Never edit files yourself.
- Manual timing includes your reaction time (rows are marked `[manual]`), so don't compare `med s` with CLI agents.
- IDE agents can often search the whole disk. Keep this kit outside any folder the IDE has open, or run the IDE in a container/VM.

**Agents you can trigger but that aren't CLIs** (an extension that watches a file or exposes a local API)
need no special mode. Write a small wrapper that starts the agent and **blocks until it's finished**, then
pass it as `--agent`. See `agents/ide_trigger_example.sh`:

```bash
python3 run.py --name my-ext --note "my-ext v1.4" --agent "$PWD/agents/ide_trigger_example.sh {workdir} {prompt_file}"
```

## The tasks

| task | type | what it probes |
|---|---|---|
| 01_pagination | bug fix, easy | off-by-one, edge cases, validation from a spec |
| 02_parse_duration | bug fix, easy | misleading error message, strict parsing |
| 03_cli_dry_run | feature, multi-file | reading 3 files, preserving existing behaviour |
| 04_config_merge | bug fix, multi-file | recursion, aliasing/mutation bugs |
| 05_no_test_edits | discipline | "make tests pass" without editing the tests |
| 06_token_bucket | implement from spec | following a written API contract exactly |

Each task folder contains `task.json` (prompt, difficulty, protected paths), `repo/` (starter code and visible tests), `hidden/` (grading tests) and `solution/` (reference fix, used by `selftest.sh`).

## Reading the report

- **pass** is the main number. The **95% CI** is a Wilson interval. If two models' intervals overlap heavily, you haven't shown a difference yet, so add runs or tasks.
- **tests%** gives partial credit and is useful for spotting "almost right" versus "lost".
- **tamper**: the model deleted a protected test file, removed or changed lines in one, or added a skip/xfail. Treat this as a red flag, not just a fail. Appending new tests or adding new test files is *not* tampering (grading uses a pristine copy of the visible tests, so additions can't help); those files are listed in `tests_added_to`.
- **med s** and **med +/-** are wall-clock time and diff size. Large diffs on small tasks usually mean collateral edits.
- **cont** is the median number of "continue" follow-ups per run (manual mode only, 0 for CLI agents). A pass that needed continues is still a pass, but a higher number means the agent needed more pushing to finish.
- **gave** is the number of runs you abandoned with `g`. Those runs are graded as they stood.
- **[manual]** after a row means the agent was driven by hand. Its **med s** includes your reaction time, so compare it only with other manual agents.
- **$ total** is the summed cost the agent itself reported. It's read from `"total_cost_usd"` in `agent.log`, which Claude Code prints with `--output-format json`. Other agents show `-`; their full output is still in `agent.log` (path in the JSONL) if they print usage some other way.

For quality beyond pass/fail, open the `workdir` of a few runs and compare `git diff` side by side **blind**: shuffle which model is which before you rate them.

## Adding your own tasks (recommended)

Six toy tasks are a smoke test. The real signal comes from 15–30 tasks taken from your own code:

1. Create `tasks/NN_name/` with `task.json`, `repo/`, `hidden/` and `solution/`.
2. A good source is a past bug-fix commit: the code before the fix goes in `repo/`, the tests added by the fix go in `hidden/`, and the fixed files go in `solution/`.
3. Write the prompt the way you'd actually ask a colleague. Put in the prompt everything the hidden tests check, so you are testing skill, not mind reading.
4. Name hidden test files `test_*.py`. Imports resolve from the repo root.
5. Run `./selftest.sh` to confirm the oracle passes and the no-op fails every task.

Aim for a mix of roughly 1/3 easy, 1/3 medium and 1/3 hard.

## Caveats

- Use at least 3 runs per task, because agents are non-deterministic.
- Keep everything else identical between models: harness, system prompt, tools, timeout.
- Hidden tests live in this folder. An agent with full disk access could go looking for them, so for strict isolation run agents in a container or VM and keep the kit outside it.
- The grader is hardened against common tricks. It runs isolated Python (`-I`) from a fresh temp dir, so a planted `pytest.py`, `sitecustomize.py` or fake `junit.xml` has no effect, and it kills the agent's whole process session before checking and grading, so leftover background jobs can't change files afterwards. It still trusts the code under test: a solution that patches pytest when imported, or a process that escapes with `setsid`, can only be stopped by running agents in a container or VM.
- Parallel runs (`--jobs` > 1) all run as your user, so a misbehaving agent could read or change another run's files while it is being graded. For a strict run, use `--jobs 1` or, better, run each agent in a container or as a separate user.
- Tasks are Python/pytest. For other languages, keep the same layout and change the grading command in `grade()` in `run.py`.
