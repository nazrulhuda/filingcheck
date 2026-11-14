# The final run: record

Provenance, times, row counts, error rows and cost only. No result is stated here.

## Commit and hashes

- Commit `da7a451e0a0ab872b2bc3f05a96699690b82d0eb`, tag `week6-measured`, checked out before the run; `git status` clean. Every one of the 3,855 rows records this commit, `git_clean: true`, and its question file's SHA-256.
- Printed before the run (`sha256sum`), each equal to its seal or the pre-registration's hash:

```
b295c38f60fcecce687f70b43520726cb0bfef3c1e616d4bd2835aeb85f343a5 *eval/questions/heldout_traps.jsonl
ab3639e64d5902c1e94328cca98bcaf5ab1596a1e232f2514a100f6a104d8b71 *eval/questions/heldout_traps_2.jsonl
7492b8775b13d8ed53b9ce2f6914085a1dfce1a7c12a3261cc87b34ed2f00ea1 *eval/PREREGISTRATION.md
```

## The runs

Each arm: `make eval SET=heldout_traps,heldout_traps_2,dev_traps,dev_unanswerable,control REPEATS=3 LABEL=final DATE=2026-11-14` with the arm's settings (`MODE=agent CHECKS=on`; `MODE=agent CHECKS=off`; `MODE=agent CHECKS=off RULES=prompt`; `MODE=baseline`; `MODE=baseline RETRIEVER=vector`). Model `openrouter:openai/gpt-oss-20b` in every row.

The arms ran one after another; **no two arms ran at the same time.** Times are UTC, 2026-11-14.

| Arm | Start | End | Rows | Error rows | Answer cost (as recorded) |
|---|---|---|---:|---:|---:|
| agent-checks-on | 07:17:45 | 07:30:28 | 771 | 2 | $0.2646 |
| agent-checks-off | 07:30:28 | 07:41:01 | 771 | 0 | $0.2519 |
| agent-prompt-rules | 07:41:01 | 07:49:34 | 771 | 2 | $0.6135 |
| baseline | 07:49:34 | 17:55:46 | 771 | 0 | $0.1377 |
| baseline-vector | 17:55:46 | 18:03:47 | 771 | 0 | $0.1272 |
| **All** | | | **3,855** | **4** | **$1.3949** |

Each arm has 84 rows for `heldout_traps`, 252 for `heldout_traps_2`, 255 for `dev_traps`, 30 for `dev_unanswerable` and 150 for `control` (257 questions × 3 runs). The two questions marked not scored were run like the others.

**The PC slept during the baseline arm**, from 07:58:29 to 17:53:51 UTC (Windows system log: Kernel-Power event 42 at 07:58:29, a wake of about one second at 11:00:02–11:00:03, Power-Troubleshooter event 1 at 17:53:51). One row was in flight: `control-117` run 1 of `2026-11-14_control_baseline-final.jsonl` (line 17). It finished normally after the wake (`finish_reason: stop`, no error), and its `latency_ms` (35,750,999) includes the sleep. Every other baseline row took under 2.5 s. No arm stopped and nothing was resumed. The last arm and the grading ran with a keep-awake request (Windows `SetThreadExecutionState`), with no settings changed.

**Error rows** (4 of 3,855; at most 1 of 30, 3.3%, in any set and arm, under the 5% limit):

| File | Question | Run | Error kind |
|---|---|---:|---|
| `2026-11-14_control_agent-checks-on-final.jsonl` | control-131 | 1 | `tool_choice_none` |
| `2026-11-14_dev_traps_agent-checks-on-final.jsonl` | dev-055 | 2 | `tool_choice_none` |
| `2026-11-14_control_agent-prompt-rules-final.jsonl` | control-131 | 3 | `tool_choice_none` |
| `2026-11-14_dev_unanswerable_agent-prompt-rules-final.jsonl` | una-008 | 2 | `cut_off` |

## Grading

After every arm had ended: `make grade SET=<set> RUN=<file> EVERY=1` on each of the 25 files, one after another, from 18:04:24 to 19:06:59 UTC; the LLM grader through its cache (`eval/llm_grades/cache.jsonl`), with a second opinion on every number-graded run. 3,851 LLM grades (every row but the 4 error rows), 1,364 of them from the cache, no grader errors; new cost as recorded $0.6655.

## Cost

As recorded in the rows and grades: answers $1.3949, grades $0.6655, total $2.0604. The OpenRouter key's own usage rose from $1.2613 (read before the run) to $2.9007 (read after the grading), $1.6394; $2.0993 of its $5 limit is left. The recorded figures come from the price table; the key's figure is what was billed.

## Files

This record, the 25 row files (`2026-11-14_<set>_<arm>-final.jsonl`), their 25 LLM grade files (`..._llm.jsonl`) and the grade cache, unedited. The commands also wrote a summary page per row file (`.md`), a summary per grade file (`_llm.md`) and five checks-off-and-on pages (`2026-11-14_final_<set>_agent-arms.md`); they hold result tables and are not in this commit.
