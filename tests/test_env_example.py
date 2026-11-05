"""`.env.example` lists every variable the code reads, and nothing the code does not read."""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_every_variable_in_env_example_is_read_somewhere() -> None:
    example = (REPO / ".env.example").read_text(encoding="utf-8")
    names = sorted(set(re.findall(r"^#?\s*([A-Z][A-Z0-9_]+)=", example, re.MULTILINE)))
    assert names, "no variables found in .env.example"
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [*(REPO / "filingcheck").rglob("*.py"), *(REPO / "filingcheck").rglob("*.yaml")]
    )
    unread = [name for name in names if name not in sources]
    assert unread == [], f"listed in .env.example but read nowhere: {unread}"
