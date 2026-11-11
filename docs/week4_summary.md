# Week 4 summary

**No accuracy claim:** six example questions prove nothing; the measurement is Week 6's. Details: [week 4 notes](week4_notes.md).

**Five checks** test `get_financial_fact` arguments against the question and our SEC data before the tool runs:
- **Company:** the company named; a name fitting two (Morgan) → reject with both.
- **Fiscal year:** an explicit year, a year-end date, "last year" or the page filter → repair; no pinned 10-K → reject.
- **Metric and period:** quarters and unsupported metrics → reject.
- **Units:** always passes, attaching the requested scale.
- **Segment:** a segment tied to the asked number → reject.

A reject goes back to the model once; a second reject by the same check ends the tool's use. Every decision is logged.

**Day 24** (6 questions × 3, 2026-11-11): checks off 13 of 18 correct, on 16. Three of those came from a check's action; the rest of the gap is the lenient clarify rule and model variance (strict rule: 12 against 14).

**Gate:** 21 scripted scenarios in CI. **Page:** the checked agent, fact chips, a "What was checked" panel, seven saved examples.

**Changed after the freeze:**
- Tickers listed with company names: nine probed companies 31 of 45 correct before, 45 of 45 after (plus 20 of 20 Coca-Cola runs after); both arms re-run.
- `search_filings` lost its `items` filter: right passage cited in 17, then 29, of 45 probe runs; both arms re-run.
- The parsers read `【1†…】` markers (no grade changed).

The prompt and tool schemas are frozen until Week 6.

**Known limits:**
- The checks cover `get_financial_fact` arguments only.
- Text answers can be confidently unsupported (Goldman's reason, Walmart's "10-year-old").
- The model sometimes gives up without searching.
- Previews show a passage's start; fact chips may show a generic line label.

**Cost:** about $0.16 ([itemized](week4_notes.md#costs)).
