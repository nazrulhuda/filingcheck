"""The statistics the pre-registration names (eval/PREREGISTRATION.md).

- A paired bootstrap clustered by question: the difference in a rate between two arms on the
  same questions, resampling questions with replacement (each question's runs stay together,
  since its rate is already the share of its runs), 10,000 resamples, a 95% percentile interval,
  seed 20261113.
- McNemar's exact two-sided test on each question's majority outcome (2 or 3 of its 3 runs).

Pure Python, no third-party code, so anyone can recompute the numbers.
"""

import math
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

SEED = 20261113
RESAMPLES = 10_000


@dataclass(frozen=True)
class Interval:
    """A difference (second arm minus first) with its 95% bootstrap interval."""

    estimate: float
    low: float
    high: float


def paired_bootstrap(
    first: Mapping[str, float],
    second: Mapping[str, float],
    *,
    resamples: int = RESAMPLES,
    seed: int = SEED,
) -> Interval:
    """The mean per-question difference `second - first`, with a 95% percentile interval.

    Each resample draws as many questions as there are, with replacement; the interval's ends
    are the nearest-rank 2.5th and 97.5th percentiles of the resampled means.
    """
    if set(first) != set(second):
        raise ValueError("a paired comparison needs the same questions in both arms")
    keys = sorted(first)
    if not keys:
        return Interval(math.nan, math.nan, math.nan)
    diffs = [second[k] - first[k] for k in keys]
    n = len(diffs)
    estimate = sum(diffs) / n
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(diffs, k=n)) / n for _ in range(resamples))
    low = means[max(0, math.ceil(0.025 * resamples) - 1)]
    high = means[max(0, math.ceil(0.975 * resamples) - 1)]
    return Interval(estimate, low, high)


def majority(runs: Sequence[bool]) -> bool:
    """True when more than half of a question's runs are true (2 or 3 of 3)."""
    return sum(runs) * 2 > len(runs)


def mcnemar_exact(b: int, c: int) -> float:
    """McNemar's exact two-sided p-value for b and c discordant pairs (a binomial test at 1/2)."""
    n = b + c
    if n == 0:
        return 1.0
    tail = float(sum(math.comb(n, i) for i in range(min(b, c) + 1))) / float(2**n)
    return min(1.0, 2 * tail)


def mcnemar(
    first: Mapping[str, Sequence[bool]], second: Mapping[str, Sequence[bool]]
) -> tuple[int, int, float]:
    """(b, c, p) on each question's majority: b yes in the first arm and no in the second."""
    if set(first) != set(second):
        raise ValueError("a paired comparison needs the same questions in both arms")
    b = sum(1 for k in first if majority(first[k]) and not majority(second[k]))
    c = sum(1 for k in first if not majority(first[k]) and majority(second[k]))
    return b, c, mcnemar_exact(b, c)
