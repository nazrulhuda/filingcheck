# Week 3 summary

**Numbers from the filings' own XBRL.** 199,899 numeric facts from the 75 pinned filings, 57,580 of them company totals, with 0 conflicts after 520 rounded copies were removed. Against SEC companyfacts:
- 1,123 agree;
- 0 disagree;
- 18 are missing from companyfacts, all of them S&P Global FY2024.

The four golden facts, read in a coding session from the printed statements (not the XBRL tags), are reproduced exactly.

**Metric coverage** (13 metrics):
- **All 75 filings:** nine metrics.
- **The rest:** shares outstanding 66, capital expenditures 69, total liabilities 60, operating income 45.
- **Nothing is derived:** a gap is reported as unavailable.

**Three tools with typed inputs:** `search_filings`, `get_financial_fact` and `calculate`. A wrong argument returns an error, and nothing is repaired.

**The agent** (LangGraph over our own client):
- **Limits:** at most 6 model calls and 8 tool calls, and no skeptical checks.
- **Where it runs:** from `make ask MODE=agent` and from `POST /ask` with `mode: "agent"`. The page still serves the baseline.

**The 8-question review:**
- **Number questions:** answered with exact values.
- **Traps:** for "Morgan" the agent picked Morgan Stanley without asking. For Nvidia's "last year" it used FY2025, though FY2026 is the latest.

**Two graded rows** (6 questions × 3 runs, deterministic grader):
- **Baseline:** 6 of 18 correct.
- **Agent:** 13 of 18 correct.

Six questions prove nothing; the rows show only that the pipeline works end to end.

**Costs:** the logged model runs this week total $0.0135.

| Run | Cost |
|---|---:|
| Tool-calling checks | $0.0012 |
| The review | $0.0020 |
| A batch test | $0.0014 |
| The graded rows | $0.0067 |
| Live API questions | $0.0022 |

**Week 4 adds:**
- the six skeptical checks;
- a retry after a rejected argument;
- the 20-question CI evaluation gate;
- the page switching to the agent.
