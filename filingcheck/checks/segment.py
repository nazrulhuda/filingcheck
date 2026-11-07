"""The segment check: a segment or product name of the argument's company in the question.

The fact tool returns company totals only, so "AWS operating income" is turned down by name
rather than answered with Amazon's total. The names are each company's `segments` list in
`data/companies.yaml`. A name of two or more words or in capitals ("AWS") is matched in any
case; a single ordinary word ("Services", "Office") only as written, so "services" in a
sentence is not Apple's Services segment. A question that asks for the company total while
mentioning a segment ("Amazon's total revenue, including AWS") passes, with a note.
"""

import re

from filingcheck.checks.base import CheckContext, CheckedCall, CheckResult

NAME = "segment"
RIGHT_QUOTE = chr(0x2019)
TOTAL_RE = re.compile(
    r"\b(?:total|consolidated|overall|company-wide|whole company|entire company|as a whole)\b",
    re.IGNORECASE,
)
_BEFORE, _AFTER = r"(?<![A-Za-z0-9])", r"(?![A-Za-z0-9])"


def _pattern(name: str) -> re.Pattern[str]:
    any_case = " " in name or (name.isupper() and len(name) >= 2)
    return re.compile(_BEFORE + re.escape(name) + _AFTER, re.IGNORECASE if any_case else 0)


def find_segments(question: str, segments: list[str]) -> list[str]:
    """The listed segment names the question uses, longest first, without overlaps."""
    text = question.replace(RIGHT_QUOTE, "'")
    spans: list[tuple[int, int, str]] = []
    for name in sorted(segments, key=len, reverse=True):
        for match in _pattern(name).finditer(text):
            if all(match.end() <= s or match.start() >= e for s, e, _ in spans):
                spans.append((match.start(), match.end(), name))
    return [name for _, _, name in sorted(spans)]


class SegmentCheck:
    """Reject a segment question for the number tool; pass a question about the total."""

    name = NAME

    def run(self, call: CheckedCall, context: CheckContext) -> CheckResult:
        """Judge the question against the argument company's segment names."""
        ticker = call.arguments["ticker"]
        company = next((c for c in context.companies if c.ticker == ticker), None)
        named = find_segments(context.question, company.segments if company else [])
        if not named:
            return CheckResult.passed(self.name, None, call.arguments, "no segment named")
        listed = ", ".join(named)
        if TOTAL_RE.search(context.question):
            reason = f"the question mentions {listed} but asks for the company total"
            return CheckResult.passed(self.name, None, call.arguments, reason)
        reason = (
            f"the fact tool returns company totals only; segment figures ({listed}) are not "
            "supported; use search_filings for the text or say so"
        )
        return CheckResult.rejected(self.name, None, call.arguments, reason)
