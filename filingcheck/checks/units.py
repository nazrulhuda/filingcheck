"""The units check: a scale the question asks for ("in millions") goes next to the raw value.

It always passes and never changes the stored value: the tool's result gains a
`requested_scale` entry with the figure converted, so the model has both.
"""

import re

from filingcheck.checks.base import CheckContext, CheckedCall, CheckResult

NAME = "units"
SCALES = {"k": "thousands", "m": "millions", "b": "billions"}
SCALE_RE = re.compile(
    r"\bin\s+(?:US\s?)?(?:\$\s?)?(?P<word>thousands|millions|billions)\b"
    r"|\bin\s+\$\s?(?P<letter>[KMB])\b"
    r"|\(\s*\$\s*in\s+(?P<paren>thousands|millions|billions)\s*\)",
    re.IGNORECASE,
)


def requested_scale(question: str) -> str | None:
    """The scale the question asks for (millions, billions or thousands), or None."""
    match = SCALE_RE.search(question)
    if match is None:
        return None
    if match["letter"]:
        return SCALES[match["letter"].lower()]
    return (match["word"] or match["paren"]).lower()


class UnitsCheck:
    """Attach the requested scale; the arguments are never changed."""

    name = NAME

    def run(self, call: CheckedCall, context: CheckContext) -> CheckResult:
        """Pass, with the requested scale as an annotation for the tool's result."""
        scale = requested_scale(context.question)
        if scale is None:
            return CheckResult.passed(self.name, None, call.arguments, "no scale asked for")
        reason = f"the user asked for {scale}; the figure in {scale} goes next to the raw value"
        return CheckResult.passed(
            self.name, None, call.arguments, reason, annotations={"requested_scale": scale}
        )
