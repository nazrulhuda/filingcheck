"""The metric-and-period check: words in the question that the annual data cannot serve.

Quarter words ("Q3", "quarterly", "three months", "first half", "H1") are rejected: the
dataset has annual 10-K figures only. Unsupported metrics ("EBITDA", "free cash flow",
"gross margin", "market cap", "dividend", ...) are rejected with the 13 supported metrics,
unless the question also names a supported metric that the argument matches ("revenue and
EBITDA" with metric revenue passes). For banks, "net revenue" and "revenue" both mean the
`revenue` metric; the lookup's bank rule picks the tag.

The check reads the sentences about the call's metric: when some sentence names that
metric, sentences that name a different metric are set aside ("What was Apple's net income
in fiscal 2025? Also, what did it report as revenue for the quarter?" passes a net income
call); a sentence that names no metric still counts ("I mean for Q3" still rejects). When
no sentence names the call's metric, the whole question is read. Known limit: one sentence
with two asks is judged as one.
"""

import re

from filingcheck.answer.citations import sentences
from filingcheck.checks.base import CheckContext, CheckedCall, CheckResult
from filingcheck.facts.metrics import METRICS

NAME = "metric"
QUARTER_RE = re.compile(
    r"\b(?:Q[1-4]|quarters?|quarterly|three months|six months|nine months|first half"
    r"|second half|half[- ]year|H[12])\b",
    re.IGNORECASE,
)
UNSUPPORTED_RE = re.compile(
    r"\b(?:EBITDA|free cash flow|gross margins?|operating margins?|market cap(?:italization)?"
    r"|share price|stock price|dividends?|headcount|employees|backlog|ARR)\b",
    re.IGNORECASE,
)
# Words that name a supported metric; longest first, so "earnings per share" is not
# "earnings" and "operating cash flow" is not "cash".
SUPPORTED: tuple[tuple[str, str], ...] = (
    ("earnings per share|diluted eps|eps", "diluted_eps"),
    ("operating cash flow|cash flows? from operations|cash from operations", "operating_cash_flow"),
    ("cash and cash equivalents|cash and equivalents", "cash_and_equivalents"),
    ("operating income|operating profit|income from operations", "operating_income"),
    ("pre-?tax income|income before (?:income )?taxes", "pretax_income"),
    ("capital expenditures?|capex", "capital_expenditures"),
    ("long-?term debt", "long_term_debt"),
    ("shares outstanding", "shares_outstanding"),
    ("total liabilities|liabilities", "total_liabilities"),
    ("total assets|assets", "total_assets"),
    ("(?:share|stock)holders'? equity|equity", "stockholders_equity"),
    ("net income|net earnings|net loss|earnings|profit|loss", "net_income"),
    ("(?:net )?revenues?|(?:net )?sales|top line", "revenue"),
    ("debt", "long_term_debt"),
    ("cash", "cash_and_equivalents"),
)
# Any word that names a supported metric, for the segment check's tie.
METRIC_WORD_RE = re.compile(r"\b(?:" + "|".join(p for p, _ in SUPPORTED) + r")\b", re.IGNORECASE)


def named_metrics(text: str) -> set[str]:
    """The supported metrics the text names (unsupported phrases removed first)."""
    text = UNSUPPORTED_RE.sub(" ", text.lower())
    found: set[str] = set()
    for pattern, metric in SUPPORTED:
        regex = re.compile(r"\b(?:" + pattern + r")\b")
        if regex.search(text):
            found.add(metric)
            text = regex.sub(" ", text)
    return found


def scoped_sentences(question: str, metric: str) -> list[str]:
    """The sentences a check about `metric` should read.

    When some sentence names the call's metric, sentences that name a different metric and
    not this one are set aside; every other sentence (this metric, or no metric) counts.
    When no sentence names the call's metric, every sentence counts.
    """
    parts = sentences(question) or [question]
    named = [named_metrics(part) for part in parts]
    if not any(metric in n for n in named):
        return parts
    return [part for part, n in zip(parts, named, strict=True) if not n or metric in n]


class MetricCheck:
    """Quarter words and unsupported metrics in the sentences about the call's metric."""

    name = NAME

    def run(self, call: CheckedCall, context: CheckContext) -> CheckResult:
        """Judge the question's period and metric words against the `metric` argument."""
        metric = call.arguments["metric"]
        text = " ".join(scoped_sentences(context.question, metric))
        quarter = QUARTER_RE.search(text)
        if quarter is not None:
            reason = (
                "the dataset has annual figures only (10-K); no quarterly periods "
                f"('{quarter.group(0)}' in the question)"
            )
            return CheckResult.rejected(self.name, "metric", call.arguments, reason)
        unsupported = sorted({m.group(0) for m in UNSUPPORTED_RE.finditer(text)})
        if unsupported:
            listed = ", ".join(f"'{u}'" for u in unsupported)
            if metric in named_metrics(text):
                reason = (
                    f"the question also asks for {listed}, which the data does not hold; "
                    f"{metric} is named too, so it is looked up"
                )
                return CheckResult.passed(self.name, "metric", call.arguments, reason)
            reason = (
                f"{listed} is not one of the 13 metrics the data holds; "
                "the supported metrics are listed"
            )
            return CheckResult.rejected(
                self.name, "metric", call.arguments, reason, options=sorted(METRICS)
            )
        return CheckResult.passed(
            self.name, "metric", call.arguments, f"an annual metric the data holds ({metric})"
        )
