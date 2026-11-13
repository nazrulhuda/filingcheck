"""The blind-graded sample that checks the LLM grader against other graders.

A fixed random sample, by seed, in strata (Week 5: 15 text answers, 15 number answers whose
deterministic grade is not `correct`, 10 that are), is written with each row's question,
answer and sources and the LLM verdict hidden. A reviewing AI session grades all of them
blind, the owner reviews ten picked by the same seed, and then the verdicts are compared.
"""

import random
from collections.abc import Iterable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    """A graded row that can be drawn: its key (file, id, run) and its stratum."""

    key: str
    stratum: str


def draw_sample(
    candidates: Iterable[Candidate], sizes: Mapping[str, int], seed: int
) -> list[Candidate]:
    """`sizes[s]` rows from each stratum `s`, the same for the same seed and pool in any order."""
    pool = sorted(candidates, key=lambda c: c.key)
    rng = random.Random(seed)
    sample: list[Candidate] = []
    for stratum, size in sizes.items():
        members = [c for c in pool if c.stratum == stratum]
        if len(members) < size:
            raise ValueError(f"stratum {stratum!r} has {len(members)} rows, fewer than {size}")
        sample += sorted(rng.sample(members, size), key=lambda c: c.key)
    return sample


def owner_subset(sample: list[Candidate], size: int, seed: int) -> list[str]:
    """The keys of the `size` rows the owner grades too, picked from the sample by the seed."""
    keys = sorted(c.key for c in sample)
    return sorted(random.Random(seed + 1).sample(keys, size))


@dataclass(frozen=True)
class HiddenRow:
    """One sampled row as the hand graders see it: everything but the LLM verdict."""

    key: str
    question: str
    expected: str  # "answer; company NKE, fiscal year 2025"
    reference: list[str]  # gold value, gold text, note lines
    answer: str
    passages: list[tuple[int, str]]  # cited passages: (number, text)
    facts: list[str]  # looked-up facts, one line each
    owner: bool = False


def render_hidden(rows: list[HiddenRow], *, title: str, intro: str) -> str:
    """The hidden file: numbered rows in the order given, no strata, the verdicts left blank."""
    parts = [f"# {title}", "", intro, ""]
    for n, row in enumerate(rows, 1):
        mark = " **[owner]**" if row.owner else ""
        parts += [
            f"## {n}{mark}",
            "",
            f"Row: `{row.key}`",
            "",
            f"**Question:** {row.question}",
            "",
            f"**Expected behavior:** {row.expected}",
            "",
            *[f"- {line}" for line in row.reference],
            "",
            "**Answer:**",
            "",
            "> " + row.answer.replace("\n", "\n> "),
            "",
            "**Cited passages:**" if row.passages else "**Cited passages:** none",
            *[f"\n[{number}] {text}" for number, text in row.passages],
            "",
            "**Numbers looked up:**" if row.facts else "**Numbers looked up:** none",
            *[f"- F{i}: {fact}" for i, fact in enumerate(row.facts, 1)],
            "",
            "Verdict: ______  Supported: ______",
            "",
        ]
    return "\n".join(parts).rstrip() + "\n"
