# Known limits

All sixteen known limits. The [README](../README.md#known-limits) lists eight of them.

- **The intervals are wide** for sets of this size (110 held-out questions); the noise between identical runs is large.
- **One model was measured** (`gpt-oss-20b`), with one prompt for the prompt-rules arm, built by code from the checks' data; a better-written prompt might do better still.
- **The checks miss phrasings they were not built for**, and some of their own actions cause failures. Of 90 failed checks-on runs read one by one, 23 came from gaps (the number tool keeps a year the model chose when the question names none; "last yr", "morgans", "american", "uniteds", "standard and poors" and "Citizens" are not read; `search_filings` has no company check) and 17 from a check's own action (asking which fiscal year for a calendar year where the question's writer accepted the nearest one; reading "the year before last" one year too far).
- **The graders are automatic:** a deterministic grader for numbers and an LLM grader for text, checked by two other automatic graders grading blind; the owner reviewed but did not grade blind. The LLM grader wrongly failed five held-out answers that gave a figure the filing states, with a citation, although the question's note accepts that. The text samples hold many easy rows.
- **The decline rule reads the checks' own refusal wordings** (widened before the final run); a refusal in other words can still be graded as an answer (listed in the report).
- **`search_filings` searches passages, not tables**, so a figure that only a table states cannot be found by search.
- **The gold values come from the same lookup the agent uses**, cross-checked against the SEC's companyfacts.
- **The development traps were written alongside the checks**, so their results are not evidence.
- The control questions were used during development: the fiscal-year check on searches was built after a dry run on them (decisions, Nov 12), so the rise in control accuracy is not held-out evidence.
- In an answer with a calculation, a figure the model writes again in its working (for example "130,497 M") is labeled Unverified, because the labeler reads figures as written.
- **Latency is from batch mode**, and the PC slept during one arm, so one run's time includes the sleep (reported apart). The live page's fallback answers, given when the main model is rate-limited, were not measured. A reranker was never built or measured.
- The checks cover the arguments of the tools, not the text of an answer. A text answer is not compared with the passage it cites, so it can be confidently unsupported: one answer gave a reason for a Goldman Sachs decision that the filing does not give, and a saved example calls Walmart's currency swaps "10-year-old", which the filing does not say. In the Week 5 dry run, a third or more of the text answers to normal questions said more than their cited passages support, and sending searches to the latest filing did not change that.
- On questions the filings do not answer (a reason a filing never gives), searching the right filing makes the model answer more often, not less: with the checks on it answered more of the 10 unanswerable questions in the final run too.
- The model sometimes says it can't find the answer without searching at all.
- A number's chip can show the metric's standard line name instead of the company's own wording ("Revenues" for Verizon's "Total Operating Revenues").
- Verified means the number is in the answer's sources, not that the sentence is right: a Verified figure can be the wrong number for the question.
