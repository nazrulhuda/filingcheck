# Hand-graded sample 1: the LLM grader against a hand grader

Sample: `2026-11-12_sample1_hidden.md` (seed 20261112). LLM verdicts: `2026-11-12_sample1_key.jsonl`, grader prompt version `1-8da4c1204b4b`. Hand grades: `2026-11-12_sample1_hand.jsonl`, made from the hidden file before any LLM verdict was seen.

The owner's ten rows (4, 12, 13, 21, 23, 26, 34, 37, 38, 39) were not graded independently by the owner, so this check has one hand grader.

| Rows | Verdict agreement | Supported agreement |
|---|---:|---:|
| All 40 | 35/40 (87.5%) | 35/40 (87.5%) |
| 15 text answers | 13/15 (86.7%) | 11/15 (73.3%) |
| 25 number answers | 22/25 (88.0%) | 24/25 (96.0%) |

**Verdict agreement is under 90%,** so the spec's rule applies: the prompt is fixed once (version 2) and a fresh sample of 40 is drawn, whose result is reported whatever it is.

## Every row where the grades differ

| Row | Stratum | Deterministic | LLM | Hand | LLM's reason | Hand grader's note |
|---:|---|---|---|---|---|---|
| 5 | number, not clean | asked_when_should_answer | wrong / n/a | asked / n/a | The question expected a direct answer, since 'last year' resolves to FY2026 per the note, but the answer asked the user which year instead. |  |
| 6 | text | not_graded | correct / yes | correct / partly | The answer states that third parties allege Netflix infringed their IP and that failure to obtain rights, defend use, or develop non-infringing technology could adversely affect its business and competitive position, matching the gold text; the litigation-cost details are also in the cited passage's context and the cited passage supports the core claims. | "costly litigation ... remove content ... licensing" is not in the cited passage |
| 9 | text | not_graded | correct / yes | partly / partly | The answer gives the gold figures: about $1.3 billion net investment at December 31, 2025, about $0.9 billion net ARS exposure, $0.4 billion hedged, USD functional currency, and remeasurement at the official rate with effects in earnings, and each claim appears in the cited passages. | says the remaining ~$0.9B exposure is unhedged; the passage says net exposure is $0.9B, of which $0.4B is hedged; "one-third" is also off |
| 20 | text | not_graded | correct / yes | correct / partly | The answer says export controls limit NVIDIA's China sales of its A100/H100-based data center products through licensing requirements, which matches the gold text, and its claims are backed by the cited passages. | the "worldwide licensing ... inventory provisions" quote is not in the cited passages |
| 24 | number, not clean | no_number | wrong / n/a | asked / no | The question expects the FY2025 total assets value (619,003 million) but the answer declines, claims no FY2025 filing exists, and asks the user instead of answering, which is not an expected refusal or clarification for this question. | asks back and falsely says there is no FY2025 filing, citing nothing |
| 25 | text | not_graded | partly / yes | correct / yes | The answer correctly names the forward, option and collar instruments and the protection of forecasted revenue, but omits the gold's other purpose of offsetting exchange risk on monetary assets and liabilities. | instruments and purpose given; the monetary-assets purpose is missing but the "how" is answered |
| 32 | number, not clean | asked_when_should_answer | wrong / n/a | asked / n/a | The question expected a direct answer, resolving 'last year' to FY2026 per the note, but the system asked the user which fiscal year instead, which is an asked response where an answer was expected. |  |
| 33 | text | not_graded | correct / partly | correct / yes | The answer gives the gold rationale of focusing on building brands and leading the bottling system, which the cited Item 1A passage states, but its added claims that refranchising aligns partners and improves efficiency are not stated in the passage, which only describes risks. | same inference wording as row 2 |

## The fix (prompt version 2)

Four patterns, one change each:

1. Rows 5 and 32: a question back where an answer was expected was graded `wrong` (the prompt's `wrong` included "asking about the wrong thing"). Version 2: it is `asked`, whatever it asks about; "asking about the wrong thing" is `wrong` only for questions that expect a question back.
2. Row 24: an answer that asks back but also states a false fact got `supported: n/a`. Version 2: `n/a` only when the answer states no fact.
3. Rows 6, 20 and 33: support for added detail went both ways. Version 2: a specific fact, figure or quoted wording not in the source text counts against support; a paraphrase or summary that follows from it does not.
4. Rows 9 and 25: a misstated relation (a hedged amount called unhedged) was graded `correct`, and a left-out side detail `partly`. Version 2: a misstated figure or relation makes it at most `partly`; a side detail left out, when the question's ask is answered, does not.
