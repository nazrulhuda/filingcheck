"""`make check-links`: every link in the README and the committed docs/ pages resolves.

A relative link must name a file or folder in the repository, read from its page's folder (an
#anchor is not checked); a web link must answer below HTTP 400. Text inside code (fenced blocks
and inline code) holds no links. A sec.gov link is asked through the project's SEC client (its
User-Agent and the shared rate limiter) with a HEAD request, so no filing is downloaded again.
"""

import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from urllib.parse import unquote, urlsplit

import httpx

from filingcheck.paths import REPO_ROOT

FENCE_RE = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.M | re.S)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
TARGET_RE = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
BARE_RE = re.compile(r"(?<![(<\"'=])\bhttps?://[^\s)<>\"'`\]]+")
TRAILING = ".,;:!?"


def strip_code(text: str) -> str:
    """The text with fenced code blocks and inline code removed."""
    return INLINE_CODE_RE.sub(" ", FENCE_RE.sub(" ", text))


def links(text: str) -> list[str]:
    """Every link target outside code, markdown links first by position, each once."""
    prose = strip_code(text)
    found: list[tuple[int, str]] = [(m.start(1), m.group(1)) for m in TARGET_RE.finditer(prose)]
    targets = {pos for pos, _ in found}
    for m in BARE_RE.finditer(prose):
        if m.start() not in targets:
            found.append((m.start(), m.group(0).rstrip(TRAILING)))
    return list(dict.fromkeys(link for _, link in sorted(found)))


def is_web(link: str) -> bool:
    """Whether the link is an http(s) address."""
    return link.startswith(("http://", "https://"))


def relative_problem(link: str, page: Path, root: Path) -> str | None:
    """Why a relative link does not resolve, or None if it does (or is not a file link)."""
    if is_web(link) or link.startswith(("#", "mailto:")):
        return None
    path = unquote(urlsplit(link).path)
    target = (page.parent / path).resolve()
    shown = Path(*(page.parent.relative_to(root).parts), path)
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return f"{Path(*_normal(shown.parts)).as_posix()} is outside the repository"
    if not target.exists():
        return f"{target.relative_to(root.resolve()).as_posix()} does not exist"
    return None


def _normal(parts: Sequence[str]) -> list[str]:
    out: list[str] = []
    for part in parts:
        if part == ".." and out and out[-1] != "..":
            out.pop()
        elif part not in (".", ""):
            out.append(part)
    return out


def check(
    root: Path, pages: Sequence[Path], web_status: Callable[[str], int | str]
) -> tuple[dict[str, tuple[int, int]], list[str]]:
    """Each page's (relative, web) link counts, and every broken link with its page.

    Each web address is asked once, however many pages link to it.
    """
    counts: dict[str, tuple[int, int]] = {}
    problems: list[str] = []
    answers: dict[str, int | str] = {}
    for page in pages:
        name = page.relative_to(root).as_posix()
        found = links(page.read_text(encoding="utf-8"))
        web = [link for link in found if is_web(link)]
        relative = [link for link in found if not is_web(link) and not link.startswith("#")]
        relative = [link for link in relative if not link.startswith("mailto:")]
        counts[name] = (len(relative), len(web))
        for link in found:
            if is_web(link):
                if link not in answers:
                    answers[link] = web_status(link)
                answer = answers[link]
                if not (isinstance(answer, int) and answer < 400):
                    shown = f"HTTP {answer}" if isinstance(answer, int) else answer
                    problems.append(f"{name}: {link}: {shown}")
            else:
                problem = relative_problem(link, page, root)
                if problem:
                    problems.append(f"{name}: {link}: {problem}")
    return counts, problems


def pages(root: Path = REPO_ROOT) -> list[Path]:
    """The README and the committed Markdown pages in docs/ (the local-only ones are not)."""
    listed = subprocess.run(
        ["git", "ls-files", "README.md", "docs/*.md"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [root / name for name in listed]


def main(argv: list[str] | None = None) -> int:
    """Check every link; print each page's counts and every broken link; 1 if any is broken."""
    from dotenv import load_dotenv

    from filingcheck.ingest.sec_client import SecClient

    load_dotenv(REPO_ROOT / ".env")
    with (
        SecClient() as sec,
        httpx.Client(
            follow_redirects=True,
            timeout=30.0,
            headers={"User-Agent": "FilingCheck link check"},
        ) as http,
    ):

        def web_status(url: str) -> int | str:
            try:
                if urlsplit(url).hostname in ("www.sec.gov", "sec.gov"):
                    return sec.head_status(url)
                return http.get(url).status_code
            except httpx.HTTPError as exc:
                return type(exc).__name__

        counts, problems = check(REPO_ROOT, pages(), web_status)
    for name, (relative, web) in counts.items():
        print(f"{name}: {relative} relative, {web} web")
    total = sum(r + w for r, w in counts.values())
    for problem in problems:
        print(f"BROKEN {problem}")
    print(
        f"check-links: {len(counts)} pages, {total} links, "
        f"{'all resolve' if not problems else f'{len(problems)} broken'}"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
