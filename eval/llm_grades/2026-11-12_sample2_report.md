# Hand-graded sample 2: the LLM grader against two blind graders

Sample: `2026-11-12_sample2_hidden.md` (seed 20261120, none of sample 1's rows). LLM verdicts: `2026-11-12_sample2_key.jsonl`, grader prompt version `2-8754c63e1ae3` (frozen).

**Graders.** Two blind graders, neither of which had seen an LLM verdict:

- the review chat, all 40 rows: `2026-11-12_sample2_review_chat_grades.md`;
- a fresh AI agent with no conversation context, given only the grader prompt and the 40 rows in one message, with no tools: prompt `2026-11-12_sample2_blind_agent_prompt.md`, raw output `2026-11-12_sample2_blind_agent_output.md`.

Plus the owner's review of the review chat's grades on his ten rows (`2026-11-12_sample2_owner_review.md`): he confirmed all ten after seeing them, so it is a review, not a blind grade. The SHA-256 of every grade file was recorded in `docs/decisions.md` before the LLM verdicts were opened.

| Pair | Verdict, all 40 | Verdict, 15 text | Supported, all 40 | Supported, 15 text |
|---|---:|---:|---:|---:|
| LLM vs review chat | 37/40 (92.5%) | 14/15 (93.3%) | 38/40 (95.0%) | 13/15 (86.7%) |
| LLM vs blind agent | 37/40 (92.5%) | 14/15 (93.3%) | 38/40 (95.0%) | 13/15 (86.7%) |
| review chat vs blind agent | 38/40 (95.0%) | 13/15 (86.7%) | 40/40 (100.0%) | 15/15 (100.0%) |
| LLM vs review chat, the owner's ten (owner reviewed) | 9/10 (90.0%) | | 9/10 (90.0%) | |

**The result:** verdict agreement with the review chat is 92.5%, at or above the spec's 90%, so the prompt stays at version 2. This is the second and last sample; no prompt change follows it.

## Every row where any grader differs

| Row | Stratum | Deterministic | LLM | Review chat | Blind agent |
|---:|---|---|---|---|---|
| 2 | text | not_graded | correct / partly | correct / partly | partly / partly |
| 19 | number, not clean (owner row) | answered_when_should_ask | asked / yes | wrong / yes | wrong / yes |
| 27 | text (owner row) | answered | wrong / yes | wrong / partly | wrong / partly |
| 35 | text | not_graded | correct / yes | partly / partly | correct / partly |
| 40 | number, clean | correct | wrong / yes | correct / yes | correct / yes |

Each grader's reason:

**Row 2.**

- LLM: The answer names the gold instruments (forward and option contracts including collars) and the forecasted-revenue purpose, but it omits the monetary assets and liabilities purpose and adds AOCI and reclassification-into-revenue details that do not appear in the cited passages.
- Review chat: the AOCI / reclassification detail is not in the cited passages shown
- Blind agent: Names forwards and options including collars and the hedging of forecasted revenue, but leaves out the gold's second purpose (offsetting exchange risk on monetary assets and liabilities); the AOCI and reclassification detail is not in the cited text.

**Row 19.**

- LLM: The question was ambiguous between Morgan Stanley and JPMorgan Chase and expected a clarifying question, but the answer instead picked Morgan Stanley and gave a figure; since an answer was not expected, the expected clarification is missing, so this is classified as asked only if a question back was given, which it was not, making it wrong.
- Review chat: owner row; answered Morgan Stanley instead of asking
- Blind agent: Picks Morgan Stanley and answers when a clarifying question about the company was expected; the figure matches F1.

**Row 27.**

- LLM: The question expects a refusal because the filing gives no reason for narrowing consumer focus, but the answer asserts a reason (additional regulations) and presents it as the explanation.
- Review chat: owner row; gives a reason the filing doesn't give; the regulation quotes are in the source, the causal claim is not
- Blind agent: A refusal was expected because the filing gives no reason, but it gives a causal reason; the regulation facts are in [5], but the claim that they caused the narrowing is not.

**Row 35.**

- LLM: The answer explains that US licensing requirements restrict Nvidia's China sales of its data center products including A100 and H100, limiting its ability to sell there, which matches the gold text; its claims about design-out, new China products and license uncertainty are in the cited passages.
- Review chat: says Nvidia itself "design[s]-out" U.S. semiconductors (the filing says customers do), and that is not in the cited passages
- Blind agent: Explains that licensing requirements restrict sales and can exclude Nvidia from the China market, consistent with gold; "design-out" of US semiconductors and some quoted wording are not in the cited passages.

**Row 40.**

- LLM: The answer gives $619,003 million, which matches the gold value of 619,003,000,000 USD scaled to millions, but it also states the raw figure as $619,003,000,000 USD, and the question asked for the value in millions, so the answer's scaling is correct and the figure is right; on reflection the answer is correct.
- Review chat: (no note)
- Blind agent: Gives $619,003,000,000, equal to $619,003 million, which matches the gold value and F1.

## Notes

- **On rows 19 and 40 the LLM's reason contradicts its own verdict.** Row 40's reason ends "on reflection the answer is correct" with the verdict `wrong`; row 19's ends "making it wrong" with the verdict `asked`. The JSON schema puts `verdict` before `reason`, so the model commits to a verdict before it reasons. Not changed here: the prompt and the grader are frozen. Proposed for Week 6: put `reason` before `verdict` in the schema, or flag rows whose reason and verdict disagree for a person.
- **Four rows (18, 20, 26, 29) come from the discarded "Moody's's" probe file** (`eval/probes/2026-11-09_names-before_discarded.jsonl`), whose question has a typo; they are kept because the sample is drawn from every stored row.
- **Rows 9 and 21 show no cited passages** because their answers cite with a dagger marker (`【1†…】`), which the parsers did not read when those rows were stored; the hidden file therefore shows "Cited passages: none" for answers that did cite a passage. All three graders marked them on that basis.
- **The sample is still easy-heavy:** many rows are identical "I can't find this" answers or clean numbers. Day 33 adds a fresh sample of 20 text answers from the dry-run rows.
