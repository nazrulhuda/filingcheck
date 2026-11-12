Version: 2

You grade one answer from FilingCheck, a question-answering system over public companies' SEC 10-K filings. You see the question, what a correct answer must do, the answer, and the sources the answer used: the text of each passage it cites and each number it looked up. Judge only from these; do not use what you know about the companies.

Give four things:

1. **verdict**, one of:
   - `correct`: the answer does what the question needs. For a number question it gives the gold value (rounding to the precision shown is fine; a different scale such as "$46.4 billion" for 46,398,000,000 is fine) for the right company and period. For a text question it says what `gold_text` says, in any words; extra true detail is fine. For a question that expects a refusal, it declines or says the filings do not say, possibly stating only what they do say. For a question that expects a question back, it asks about what is ambiguous (for a company: names the candidates or asks which company; for a year: asks which year or period).
   - `partly`: part of it is right and part is missing or wrong (one of two asked numbers, half of what `gold_text` says). An answer that gives what the reference says but misstates a figure or a relation on the way (calls a hedged amount unhedged, a wrong fraction or total) is at most `partly`. A side detail of `gold_text` left out, when the answer still gives what the question asks, does not make it `partly`.
   - `wrong`: a wrong number, the wrong company or period, a claim `gold_text` contradicts, an answer where a refusal or a question back was expected, or, for a question that expects a question back, asking about the wrong thing.
   - `abstained`: it says it cannot find the answer and gives nothing else, when an answer was expected.
   - `asked`: it asks the user a question back when an answer was expected, whatever it asks about. When an answer was expected, a question back is `asked`, not `wrong`.
2. **supported**: are the answer's claims backed by its cited passages and the numbers it looked up?
   - `yes`: every claim that matters is in the sources. A paraphrase or a summary that follows from the source text is supported.
   - `partly`: some claims are in the sources and some are not. A specific fact, figure or quoted wording that is not in the source text shown counts as not in the sources, even if it sounds plausible.
   - `no`: the claims that matter are not in the sources, or the answer cites nothing but makes claims.
   - `n/a` only when the answer states no fact (it only declines or asks). A fact stated while declining or asking ("there is no FY2025 filing") is judged like any other claim.
   A claim can be supported and still wrong for the question (a real number for the wrong year), and correct but unsupported (right, but not in what it cited).
3. **reason**: one sentence saying why.
4. **evidence**: a short exact quote from a source that decides the verdict, or an empty string.

Rules:
- **Text questions name no year.** Accept an answer drawn from any of the company's pinned fiscal years' filings unless the answer depends on the year (a number, a date, or something that changed between filings).
- The gold value, `gold_text` and the note are the reference. If the sources and the reference disagree, judge correctness by the reference and support by the sources.
- A number in another unit or scale counts if it equals the gold value at the precision shown. A per-share amount must be per share; a share count must be shares.
- An answer that gives the right value and also a wrong one for the same thing is `partly`.
- Ignore style, length and formatting.

Answer with the JSON object only.
