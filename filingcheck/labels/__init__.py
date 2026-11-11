"""Number labels: Verified, Conflict or Unverified for every figure in an answer.

Each figure is checked against the SEC data the answer's run used. Deterministic and pure: no
network, no model.

A figure is read with the grader's number reader (`filingcheck.eval.grade.read_figures`), so
the labeler and the grader read numbers the same way. Money amounts, plain numbers of 100 or
more, decimals, percentages and per-share amounts get a label; years, dates, citation markers,
Item numbers and list numbers do not. A range gets one label per end.

A figure matches a source value when they agree to the precision shown ("$1.3 billion" covers
$1.25 billion up to, not including, $1.35 billion) and their signs agree. The rules, first
match wins:
1. Verified, fact: a fact the run's `get_financial_fact` returned.
2. Verified, fact for another period: the same concept as a returned fact, for another annual
   period or year end in the same filing; the label names the period.
3. Verified, calculation: a `calculate` result from the run whose inputs each match a returned
   fact or a figure in a cited passage.
4. Verified, passage: a figure in a passage the answer cites.
5. Conflict: in a sentence that cites a fact ([Fn]), of the same kind as that fact (money,
   per-share or shares), and matching no source; the label carries the cited fact's value.
6. Unverified: anything else, and every figure of an answer that cites nothing.

What a label does not prove: "Verified" means the figure is in a cited SEC source. It does not
prove the sentence uses it correctly; an answer can quote a real number for the wrong year or
the wrong company. Correctness is the grader's job.
"""

from filingcheck.labels.label import (
    FilingFacts,
    NumberLabel,
    SourceCalculation,
    SourceFact,
    SourcePassage,
    Sources,
    label_numbers,
)

__all__ = [
    "FilingFacts",
    "NumberLabel",
    "SourceCalculation",
    "SourceFact",
    "SourcePassage",
    "Sources",
    "label_numbers",
]
