"""`make check-links`: the links in the README and the committed docs pages, found outside code,
relative ones resolved against the repository and web ones asked for their status."""

from pathlib import Path

from filingcheck.links import check, links, relative_problem

PAGE = """# Title

See [the report](eval/results/report.md#section) and ![a chart](docs/results/chart.png).
[![CI](https://github.com/o/r/actions/workflows/ci.yml/badge.svg)](https://github.com/o/r/actions)
A bare link: https://arxiv.org/abs/2608.10213. And [a section](#title), [mail](mailto:a@b.c).

```bash
make run   # http://localhost:8000
```

The base URL is `https://api.example.com/v1`; [a doc](../README.md "the readme").
"""


def test_links_are_found_outside_code_in_order_once_each() -> None:
    assert links(PAGE) == [
        "eval/results/report.md#section",
        "docs/results/chart.png",
        "https://github.com/o/r/actions/workflows/ci.yml/badge.svg",
        "https://github.com/o/r/actions",
        "https://arxiv.org/abs/2608.10213",
        "#title",
        "mailto:a@b.c",
        "../README.md",
    ]


def test_a_relative_link_must_name_a_file_or_folder_from_its_pages_folder(tmp_path: Path) -> None:
    (tmp_path / "docs" / "results").mkdir(parents=True)
    (tmp_path / "docs" / "results" / "chart one.png").write_bytes(b"")
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    page = tmp_path / "docs" / "page.md"
    assert relative_problem("results/chart%20one.png", page, tmp_path) is None
    assert relative_problem("../README.md#how-to-run", page, tmp_path) is None
    assert relative_problem("results", page, tmp_path) is None
    assert relative_problem("#a-heading", page, tmp_path) is None
    assert relative_problem("mailto:a@b.c", page, tmp_path) is None
    assert relative_problem("missing.md", page, tmp_path) == "docs/missing.md does not exist"
    assert (
        relative_problem("../../outside.md", page, tmp_path)
        == "../outside.md is outside the repository"
    )


def test_check_reports_each_broken_link_with_its_page(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text(
        "[ok](docs/a.md) [gone](docs/gone.md) https://example.com/ok https://example.com/404",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "a.md").write_text("https://example.com/ok", encoding="utf-8")
    asked: list[str] = []

    def status(url: str) -> int | str:
        asked.append(url)
        return 404 if url.endswith("404") else 200

    counts, problems = check(tmp_path, [tmp_path / "README.md", tmp_path / "docs" / "a.md"], status)
    assert problems == [
        "README.md: docs/gone.md: docs/gone.md does not exist",
        "README.md: https://example.com/404: HTTP 404",
    ]
    assert asked == ["https://example.com/ok", "https://example.com/404"]  # each web link once
    assert counts == {"README.md": (2, 2), "docs/a.md": (0, 1)}
