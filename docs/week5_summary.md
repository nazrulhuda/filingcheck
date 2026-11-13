# Week 5 summary

**No accuracy claim:** every number here is from the development sets, a pipeline check with no interval; the measurement is Week 6's. Details: [week 5 notes](week5_notes.md).

**Labels:** every figure in an answer is Verified (in a cited fact or passage), Conflict or Unverified, computed after the model. Verified means the number is in a cited source, not that the sentence is right.

**Four question sets:** `dev_traps` (85), `dev_unanswerable` (10), `control` (50, in FinanceBench's three styles), and `heldout_traps` (28), written by a fresh AI agent that saw only the category names and the company list, sealed by SHA-256 and unrun until Week 6.

**Graders:** the deterministic grader for numbers (strict clarify rule; re-grading 314 stored rows changed 10), and an LLM grader of another model family for text, with a second opinion on failed number grades. Its check: two blind AI graders and the owner's review, 37 of 40 verdicts on sample 2 after one prompt fix (then frozen); 16 of 20 on text answers.

**Dry run** (145 questions, 3 runs, both arms): no false repairs on control questions; 10 relative-year runs made no tool call; a third or more of text answers say more than their passages support. It found the agent searching fiscal 2023 on 124 of 159 text-question calls, so the fiscal-year check now runs on `search_filings` (added after the freeze, both arms re-run): control abstains fell 21 to 12 and every search went to the latest filing; text support did not improve, and the unanswerable set got worse (5 of 30 answered, against 1).

**Noise:** identical code moved 5 of 255 rows between runs.

**Known limits:** text support; unanswerable questions answered from the latest filing; a refusal quoting a percentage graded as an answer; one decline wording missed.

**Cost:** about $0.81 ([notes](week5_notes.md)).
