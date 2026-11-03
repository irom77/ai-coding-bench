# TODO: harder tasks

**Why:** the six bundled tasks are a smoke test. On the first leaderboard, two of the four agents scored
18/18 and every 95% interval overlaps, so the tasks can't rank strong agents. Only `04_config_merge`
separated them. The next set should be harder, closer to real work, and **kept private** (outside this
public repo) so models can't have seen them during training.

Target: 15–30 tasks, roughly ⅓ medium / ⅓ hard / ⅓ very hard, each with hidden tests, a reference
solution and an oracle that passes in `./selftest.sh`.

## New task types

| # | Task type | What it probes | Example |
|---|---|---|---|
| 1 | **Find the bug in a bigger repo** | navigation, reading code they didn't write | 30–50 file project; the bug report names a symptom, not a file |
| 2 | **Bug from a stack trace / log** | debugging from evidence, reproducing first | prompt is a user report + traceback; root cause is two calls away from where it crashes |
| 3 | **Multi-file refactor, behaviour preserved** | consistency across files, not breaking callers | rename/split a module and keep the old import path working with a deprecation warning |
| 4 | **Concurrency bug** | reasoning about races and locking | thread-safe cache or worker pool that loses updates; hidden tests are deterministic (injected scheduling) |
| 5 | **Performance fix under a budget** | algorithmic thinking, measuring | O(n²) code that must handle 1M items in < 1 s; hidden tests time it and check results |
| 6 | **Spec with many edge cases** | careful reading, completeness | semver range matcher, cron expression parser, CSV dialect handling |
| 7 | **API / dependency migration** | adapting to a changed interface | move code off a deprecated API to its replacement without changing behaviour |
| 8 | **Fix a flaky test's root cause** | discipline: fix code, not tests | test depends on time, ordering or global state; editing the test counts as tampering |
| 9 | **Security fix** | recognising and closing a vulnerability fully | path traversal or SQL injection; hidden tests include bypass variants of the exploit |
| 10 | **Feature across layers** | longer tasks, keeping everything consistent | new CLI subcommand + config option + docs + tests, all working together |
| 11 | **Non-Python task** | breadth beyond Python | the same kind of bug in TypeScript or Go (needs a per-task grading command) |
| 12 | **Honesty probe: impossible or contradictory spec** | saying "can't" instead of faking it | requirements conflict; pass = code unchanged + the agent explains the conflict (needs a new grading mode) |

## Runner changes these tasks need

- [ ] **Per-task grading command** in `task.json` (for TypeScript/Go tasks, timing checks).
- [ ] **Per-task timeout** in `task.json`, since hard tasks need more than the 300 s default.
- [ ] **Private task directory**: `--tasks-dir PATH` so the real task set can live outside this public repo.
- [ ] **"Claimed vs. did" check**: flag runs where the agent's final message says it changed or tested something
      but the diff is empty or no test command ran. Codex did exactly this on `04_config_merge`.
- [ ] **Grading mode for honesty probes**: pass when nothing was changed and the final message names the conflict.
- [ ] **Difficulty column** on the leaderboard (pass rate per easy / medium / hard).
