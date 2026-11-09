"""The segment check: a segment or product figure asked of the number tool.

The fact tool returns company totals only, so "AWS revenue" is turned down by name rather
than answered with Amazon's total. The names are each company's `segments` list in
`data/companies.yaml`; a name of two or more words or in capitals ("AWS") is matched in any
case, a single ordinary word ("Services", "Office") as written, or in any case directly before
a metric word ("services revenue"), so "revenue from products and services" is not a segment.

A segment name alone is not enough: it must be tied to the number, meaning within three
words of a metric word in the same sentence, before or after it ("AWS revenue", "revenue did
AWS make", "revenues in the Commercial & Investment Bank", "AWS's total revenue"). "Including"
or "included" next to the segment breaks the tie, since the segment is then part of the total
("Amazon's total revenue, including AWS", "including AWS revenue"); "excluding" keeps it.
Only the sentences about the call's metric are read (see `metric.scoped_sentences`). A
segment eight words from the metric ("the revenue for the company that makes the iPhone"), in
another sentence, or of another company is not a segment question.
"""

import re

from filingcheck.checks.base import CheckContext, CheckedCall, CheckResult
from filingcheck.checks.metric import METRIC_WORD_RE, scoped_sentences

NAME = "segment"
RIGHT_QUOTE = chr(0x2019)
WINDOW = 3  # at most this many words between the segment and the metric word
INCLUDE_RE = re.compile(r"\b(?:including|included|includes|inclusive of)\b", re.IGNORECASE)
# "including" right before the segment, with at most "the" between: "including the AWS revenue".
INCLUDED_BEFORE_RE = re.compile(
    r"\b(?:including|includes|inclusive of)\s+(?:the\s+)?$", re.IGNORECASE
)
WORD_RE = re.compile(r"[A-Za-z0-9$%&'./-]+")
_BEFORE, _AFTER = r"(?<![A-Za-z0-9])", r"(?![A-Za-z0-9])"


def _any_case(name: str) -> bool:
    return " " in name or (name.isupper() and len(name) >= 2)


def _patterns(name: str) -> list[re.Pattern[str]]:
    if _any_case(name):
        return [re.compile(_BEFORE + re.escape(name) + _AFTER, re.IGNORECASE)]
    before_metric = r"(?=\s+" + METRIC_WORD_RE.pattern + ")"
    return [
        re.compile(_BEFORE + re.escape(name) + _AFTER),
        re.compile(_BEFORE + re.escape(name) + before_metric, re.IGNORECASE),
    ]


def _segment_spans(sentence: str, segments: list[str]) -> list[tuple[int, int, str]]:
    """Where the listed segment names appear, longest first, without overlaps."""
    spans: list[tuple[int, int, str]] = []
    for name in sorted(segments, key=len, reverse=True):
        for pattern in _patterns(name):
            for match in pattern.finditer(sentence):
                if all(match.end() <= s or match.start() >= e for s, e, _ in spans):
                    spans.append((match.start(), match.end(), name))
    return sorted(spans)


def _tied(sentence: str, start: int, end: int) -> bool:
    """True if a metric word sits within WINDOW words of the segment, with no 'including'."""
    if INCLUDED_BEFORE_RE.search(sentence[:start]):
        return False  # "including AWS revenue": the segment is part of the total asked for
    for metric in METRIC_WORD_RE.finditer(sentence):
        if metric.end() <= start:
            between = sentence[metric.end() : start]
        elif end <= metric.start():
            between = sentence[end : metric.start()]
        else:
            continue
        if len(WORD_RE.findall(between)) > WINDOW:
            continue
        after = sentence[end:].lstrip(" ,;:")
        if INCLUDE_RE.search(between) or INCLUDE_RE.match(after):
            continue
        return True
    return False


def find_segments(
    question: str, segments: list[str], metric: str = "revenue"
) -> tuple[list[str], list[str]]:
    """The segment names in the sentences about `metric`: those tied to the number, and the rest."""
    text = question.replace(RIGHT_QUOTE, "'")
    tied: list[str] = []
    loose: list[str] = []
    for sentence in scoped_sentences(text, metric):
        for start, end, name in _segment_spans(sentence, segments):
            bucket = tied if _tied(sentence, start, end) else loose
            if name not in bucket:
                bucket.append(name)
    return tied, [name for name in loose if name not in tied]


class SegmentCheck:
    """Reject a segment figure asked of the number tool."""

    name = NAME

    def run(self, call: CheckedCall, context: CheckContext) -> CheckResult:
        """Judge the question against the argument company's segment names."""
        ticker = call.arguments["ticker"]
        company = next((c for c in context.companies if c.ticker == ticker), None)
        named, loose = find_segments(
            context.question, company.segments if company else [], call.arguments["metric"]
        )
        if not named:
            reason = (
                f"the question mentions {', '.join(loose)} but asks for the company figure"
                if loose
                else "no segment tied to the number"
            )
            return CheckResult.passed(self.name, None, call.arguments, reason)
        listed = ", ".join(named)
        reason = (
            f"the fact tool returns company totals only; segment figures ({listed}) are not "
            "supported; use search_filings for the text or say so"
        )
        return CheckResult.rejected(self.name, None, call.arguments, reason)
