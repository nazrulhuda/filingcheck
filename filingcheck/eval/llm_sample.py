"""The hand-graded sample that checks the LLM grader against people.

A fixed random sample, by seed, in strata (Week 5: 15 text answers, 15 number answers whose
deterministic grade is not `correct`, 10 that are), is written with each row's question,
answer and sources and the LLM verdict hidden. The review chat grades all of them by hand, the
owner grades ten picked by the same seed, and then the verdicts are compared.
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
