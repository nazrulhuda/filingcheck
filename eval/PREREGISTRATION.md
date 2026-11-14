# Pre-registration: the Week 6 measurement

**Who wrote this and when.** The definitions below were written by a reviewing AI session on 2026-11-12 and 2026-11-13, not by the code's author. That was after the first held-out questions and their gold values had been reviewed (2026-11-12), and before any held-out answer existed. They are copied here with plain-English edits only; no meaning was changed. This file is merged before the first final row is written, and it does not change after that: anything added after the results is marked "added after the results" in the report. Its SHA-256 is in the pull request that adds it.

## What was decided before the run, and when

- **The arms**, five, on the same questions, 3 runs per question each:
  - `baseline-vector`: one model call over the top 8 passages from vector search; no tools, no checks.
  - `baseline`: the same with hybrid search.
  - `agent-checks-off`: the agent with its three tools, no checks.
  - `agent-prompt-rules`: the agent with the checks off and the checks' rules written into its system prompt, built by code from the data the checks read.
  - `agent-checks-on`: the deployed system.
  - "+number labels" is no new run: the labels do not change an answer, so this row re-counts the agent arms' confidently-wrong rate with and without them.
  - A reranker was never built and is not measured. A stronger-model row may be run later on the same tagged commit and scored by these rules, marked "added later".
- **The settings:** the deployed ones (`openrouter:openai/gpt-oss-20b` on Groq, temperature 0.6, reasoning effort low, max_tokens 700, hybrid retrieval with k 8 for the agent), batch mode with no fallback model. The live page can answer with a fallback model when the main one is rate-limited; those answers are not measured.
- **The question sets:** the two sealed held-out files, the development traps (`dev_traps`, 85), the development unanswerable set (`dev_unanswerable`, 10) and the control set (`control`, 50).
- **The held-out set grew from 28 to 112 questions before anything was run.** A simulation on the Week 5 development rows (resampling development questions in the held-out set's mix of types) gave about a 1 in 10 chance that 28 questions show a clear difference in the confidently-wrong rate, and about 8 in 10 with 112. It is rough: the pools are small, and it assumes held-out questions behave like development ones. The decision was made on 2026-11-12, after the development results and before any held-out answer existed.
- **The two held-out files and their seals:**
  - `eval/questions/heldout_traps.jsonl` (28 questions, `held-001` to `held-028`), written on 2026-11-12 by an AI agent launched from the coding session. Its prompt held only the question template (the seven category names, the companies and years, the metrics), but the agent also received the project's description file, which names the five checks and the goal; it saw no development question, gold value or verdict. Sealed on 2026-11-12 at SHA-256 `456723d5ca80eece53af096cc0516b6105e09772c8c52b45e4e1e5f7b72ec014`. On 2026-11-13, before any held-out run, it changed only by four refusal notes (held-018, held-019, held-021, held-022: an answer that gives a figure the filing states, with a citation, is also acceptable, and the LLM grader decides), added after a test showed the LLM grader accepts a correct cited figure and rejects a plainly wrong one. Its seal is now `b295c38f60fcecce687f70b43520726cb0bfef3c1e616d4bd2835aeb85f343a5`.
  - `eval/questions/heldout_traps_2.jsonl` (84 questions, `held-029` to `held-112`), written on 2026-11-13 by Google Gemini (`gemini-3.8-flash`) through its API, outside the coding session: one request whose only message was the question template with the 28 used questions listed. Sealed on 2026-11-13 at SHA-256 `ab3639e64d5902c1e94328cca98bcaf5ab1596a1e232f2514a100f6a104d8b71`.
  - Both seals are checked before the run; a test pins them.
- **Not scored:** held-045 (no gold: Nike's filing reports no operating-income line) and held-048 (it repeats development question dev-017) are run and left out of every rate, decided before either file was sealed or run. So the held-out set has 110 scored questions.
- **One primary outcome:** on the held-out questions, checks on against checks off, the confidently-wrong rate. Wrong-argument calls are reported as how the checks work, not as a second headline: with the checks on, a stopped call never runs.

## The definitions

**Runs and rates.**
- A run is one question asked once in one arm. Every question is asked 3 times per arm.
- A rate is computed per question first (the share of its 3 runs), then averaged over the questions, so every question weighs the same.
- Error rows stay in the count: never correct, never confidently wrong. If an arm has more than 5% error rows, stop and ask.

**Which grader decides.**
- Text-graded runs are decided by the LLM grader (prompt v2, frozen). They are:
  - questions with `gold_text` (the control text questions);
  - `unanswerable_text` questions;
  - rows the deterministic grader marks `llm_decides`.
- Every other run is number-graded, decided by the deterministic grader (strict clarify rule).
- The LLM's verdict on a number-graded run is a second opinion. It is reported, and never changes a grade.

**1. Accuracy.**
- A run is correct when the deciding grader says so:
  - deterministic outcome `correct` (for a question with `also_accept`, under either expectation, as the grader already does);
  - or LLM verdict `correct`.
- `partly` is not correct; it is shown apart.

**2. Confidently wrong.** A run is confidently wrong when both of these hold:
- **(a) It gives a wrong answer instead of declining or asking:**
  - deterministic outcome `wrong_number`, `other_year_number` or `answered_when_should_ask`;
  - or, for a text-graded run, LLM verdict `wrong`.
- **(b) It carries no warning on its key number:** at least one key figure has no Conflict or Unverified label.
  - The key figures are the figure the grader matched, for `other_year_number`; otherwise every figure the grader counted as an amount.
  - A figure with no label carries no warning.
  - A run with no such figures carries no warning (labels cover figures, not sentences).

Not confidently wrong: abstains, asks, `no_number`, `year_not_stated`, `partly`, errors.

Also reported:
- for the "+number labels" row: the same rate with (b) left out;
- **a sensitivity line, both graders:** number-graded runs that are confidently wrong and whose LLM second opinion is also `wrong`. (On the development dry run the two graders agreed on 43 of 46 such runs with the checks off and 11 of 18 with them on, so the main rate is the stricter one for the checks-on arm.)

**3. Wrong-argument calls per 100 runs.**
- Only `get_financial_fact` calls are counted, and only calls the tool ran: calls stored with status `ok`. A call stopped by a check (reject) or by input validation is stored with status `error` and did not run. (In the Week 5 dry-run rows every non-ok number-tool call is a check reject. If the final rows hold another kind of error, list them and ask.)
- The arguments compared are the ones the tool ran with, after any repair (the stored call's `arguments`).

A call that ran is a wrong-argument call when:
- **The question expects an answer and has a numeric gold** (company C, fiscal year Y): its ticker is not C, or its fiscal year is not Y.
  - The metric is not compared. A call for another metric of the right company and year is not counted.
  - If the question's `also_accept` gives another fiscal year (held-007), that year is right too.
- **The question expects clarify or refuse and its `company` is null** (the name fits two companies, or none of the 25): every call that ran counts, since any company was a guess.
  - Except when the question carries a page filter (dev-011, dev-025, dev-085): no call is counted. These test a conflict between the page's filter and the question, not a guessed name, and a call for the filter's company is not a guess. No held-out question has a page filter. *(Added Nov 13, found in a code review.)*
- **The question expects clarify and names company C** (the year is the unclear part): its ticker is not C.
- **Any other question** (refusals that name a company, including `segment_vs_total` refusals; text questions): no call is counted.
  - Why segment refusals are left out: fetching the company total is not wrong by itself. In the Week 5 dry run, 7 of the 9 such calls with the checks off came before a correct answer. Counting them would make the checks look better partly by definition. They are reported apart (below).

How it is reported:
- The rate is wrong-argument calls per 100 runs (per question: its count over its 3 runs, then averaged).
- With the checks on, a stopped call does not run, so this rate falls partly by design. The report says so next to the number.
- Also reported:
  - the same count on the arguments as the model sent them (each call records them from 2026-11-13; with the checks off they equal what ran);
  - of the wrong-argument calls as sent with the checks on: how many were repaired, how many rejected, how many ran unchanged;
  - the count per 100 calls that ran;
  - on `segment_vs_total` refusals for company C and metric M: calls for C and M that ran, per 100 runs.
- The baseline arms make no tool calls: shown as n/a.

**4. Abstain rate.**
- The share of runs with deterministic outcome `abstained` (for `unanswerable_text`: classified as declined).
- Asking a question back is not abstaining; asks are shown in the outcome table.

**5. False repairs on control questions.**
- Control runs in which a check repaired or rejected a `get_financial_fact` call, per 100 control runs, each listed with its reason.
- The fiscal-year check's repairs on `search_filings` for control questions that name no year are listed apart: that is its design.

**6. Latency.**
- p50 and p95 of `latency_ms` per set and arm.
- Batch mode: if the client waited out a rate limit inside a run, that wait is in the time. The live page's own p50 and p95 (from `/stats`) are shown apart.

**7. Cost.**
- The sum of `cost_usd` per set and arm, and per 100 questions.
- The LLM grader's cost apart.

**Comparisons.**
- **Paired intervals.** Every comparison is paired (the same questions in two arms).
  - The difference in a rate gets a 95% interval from a paired bootstrap that resamples questions, keeping each question's 3 runs together.
  - 10,000 resamples, percentile interval, seed 20261113.
- **McNemar.** Accuracy and confidently wrong also get McNemar's exact two-sided test on each question's majority outcome (2 or 3 of its 3 runs); report b, c and p.
- **Held-out** means both sealed files together (110 scored questions: 112 less the two marked not scored). The two files are also shown apart, because they had different writers (the first saw the project's description file; the second was written outside the project). If the two files' differences point in opposite directions, the README says so in its first results paragraph.
- **Primary (decided now):** held-out, `agent-checks-on` against `agent-checks-off`, the confidently-wrong rate.
  - A reduction is claimed only if the 95% interval of the difference lies entirely below zero.
  - Everything else is descriptive: 95% intervals, and no claim beyond them.
- **Secondary, named now:**
  - (S1) held-out, `agent-checks-on` against `agent-prompt-rules`: confidently wrong and accuracy;
  - (S2) held-out, checks on against off: wrong-argument calls per 100 runs;
  - (S3) held-out, checks on against off: accuracy;
  - (S4) the both-graders sensitivity line for the primary comparison;
  - (S5) the primary comparison with every error row counted as confidently wrong (the worst case for the checks; capped runs fail more often with the checks on).
- **Development beside held-out:** the same comparisons on `dev_traps`, labelled "development: the checks were built while looking at these questions".
- **Pooling:** no pooled headline unless held-out and development agree.
  - Agree means: the differences have the same sign, and each set's estimate lies inside the other's 95% interval.
  - If they agree, one pooled line (all trap questions, same bootstrap) may follow the two, never replace them.
- **If the held-out set does not confirm:**
  - if its interval includes zero, the README says the held-out questions do not confirm the development result, and gives both;
  - if its estimate goes against the checks, the README says so in its first results paragraph.
- **The prompt-rules comparison (S1) is stated whichever way it comes out,** in the README's results section:
  - if the checks-on arm is better with the interval clear of zero: "the server-side checks did better than the same rules given as instructions";
  - if the interval includes zero: "on these questions, the same rules written into the prompt did about as well as the server-side checks; the checks add enforcement that does not depend on the model following instructions, and a log of every decision", with the prompt-injection category shown apart;
  - if the prompt-rules arm is better: say so first.
- **Ablation steps** (each paired, 95%, descriptive):
  - baseline-vector → baseline;
  - baseline → agent-checks-off;
  - agent-checks-off → agent-prompt-rules;
  - agent-checks-off → agent-checks-on;
  - checks-on without labels → with labels (confidently wrong only).
- **Control:** accuracy, checks on vs off, with its interval. "No harm" is said only as far as the interval shows; with 50 questions it cannot rule out a few points.
- **The calendar-year questions** (held-006, held-044, held-049) count as written: their writers accept the nearest fiscal year, and the frozen fiscal-year check asks which fiscal year instead. One extra line gives the held-out results without them.
- **"Do you mean X?" on a one-candidate name** (held-004, held-032, held-035: "american", "united", where only one matching company is covered): the strict clarify rule does not count a question back that names one company, so these can fail under it while passing the lenient rule. They count as written; the report shows the three under both rules. An ask is never confidently wrong, so the primary outcome is not affected.
- **Not scored:** a question marked `"scored": false` in its file, with a reason, is left out of every rate and listed in the report: held-045 (no gold: Nike reports no operating-income line) and held-048 (it repeats development question dev-017, "nvidia net income 2024", so it is not held-out evidence). Decided at the Day 37 review, before either file was sealed or run.
- **Noise:**
  - per set and arm, the share of questions whose 3 runs do not all get the same outcome;
  - the Week 5 re-run of identical code (182 → 177 of 255).
- **Always-abstain floor:** the abstain sentence ("I can't find this in the filings I have.") graded as the answer to every question by the same graders.
  - Its accuracy per set is shown beside the arms.
  - Its confidently-wrong rate is 0 by definition.
- **The graders:**
  - (i) number-graded runs where the LLM's verdict disagrees with the deterministic grade, counted;
  - (ii) every row whose LLM reason contradicts its verdict, found with a keyword list and confirmed by reading;
  - (iii) the blind check of 30 text verdicts drawn by seed from the final checks-on rows, graded blind by Google Gemini through its API outside the project and by a reviewing AI session, before the LLM verdicts are shown;
  - (iv) refusals the decline rule missed, listed;
  - (v) runs on refusal questions that gave a figure from a cited passage or table, listed with the grade each got.
- **The headline sentence**, filled in from the results and used as written: "On N held-out trap questions (3 runs each), turning the checks on changed the confidently-wrong rate from A% to B% (difference D points, 95% interval L to U)." Then the development numbers, the prompt-rules sentence, and the sentences the pooling and confirmation rules call for.
- **A row added later** (a stronger model, or questions written by a person) uses these definitions unchanged and is marked "added later".

**Per-run CSV columns:** set, id, repeat, arm, category, expected_behavior, graded_by (number or text), outcome, llm_verdict, correct, confidently_wrong, confidently_wrong_no_labels, confidently_wrong_both_graders, wrong_arg_ran, wrong_arg_sent, segment_total_calls, calls_ran, abstained, false_repair, latency_ms, cost_usd, error.

## How the code reads seven of the definitions

These follow from the definitions above; they are written down so a reader can check them.

- **Wrong-argument calls as sent** use each call's `sent_arguments`, with the page filter's defaults filled in as the agent fills them before the checks (so with the checks off they equal what ran), over every number-tool call the model sent that ran or was stopped by a check. The breakdown counts a stopped call as rejected, a call that ran with arguments that differ from the ones sent as repaired, and the rest as run unchanged.
- **Confidently wrong with both graders** applies to number-graded runs; a text-graded run has one deciding grader, so for it this equals the main rate.
- **The bootstrap interval's ends** are the nearest-rank 2.5th and 97.5th percentiles of the 10,000 resampled means; the code is `filingcheck/eval/stats.py`, and the metrics are `filingcheck/eval/metrics.py`.
- **The graders disagree** (graders item i) when one passes a number-graded run and the other fails it: the deterministic outcome is `correct` and the LLM's second opinion is not, or the other way round. Every pairing of the two (such as `asked` against `asked_when_should_answer`) is shown in a table beside the count.
- **Noise** compares the deciding grader's outcome across a question's runs: the deterministic outcome for a number-graded run, the LLM verdict for a text-graded one, `error` for an error row.
- **Wrong-argument calls per 100 calls that ran** is the arm's total of such calls over its total of calls that ran (a pooled ratio: a question with no call has no share of its own). The rate per 100 runs is per question first, like every rate.
- **The second opinion covers every number-graded run in the final run**, passed or failed (`make grade ... EVERY=1`), with the same frozen grader prompt, which does not mention the deterministic grade; it changes no grade. Graders item (i) counts both directions: the deterministic grader passes and the LLM fails, and the other way round. Rows graded earlier, the Week 5 dry run's included, have a second opinion only on the runs the deterministic grader failed, so only one direction can show there.
