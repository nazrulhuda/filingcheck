"""Terminal output for commands that print model or filing text."""

import sys
from typing import TextIO


def use_utf8_output(*streams: TextIO) -> None:
    """Write UTF-8 to the given streams (default stdout and stderr).

    Windows writes to a pipe in cp1252, which cannot encode characters models use, such as
    the non-breaking hyphen. A stream that cannot be reconfigured is left as it is.
    """
    for stream in streams or (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")
