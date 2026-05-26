"""Design-of-experiments sampling over the (alloy x coating x ceramic) catalog.

Three samplers:
- full_factorial: all combinations
- lhs: Latin hypercube on the discrete index space
- sobol: low-discrepancy Sobol sequence (via scipy)

All samplers return list[Combo] of length n (or full catalog for factorial).
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.stats import qmc

from .schemas import Combo
from . import catalog as _catalog


def full_factorial(
    alloys: Sequence = _catalog.ALLOYS,
    coatings: Sequence = _catalog.COATINGS,
    ceramics: Sequence = _catalog.CERAMICS,
) -> list[Combo]:
    return [Combo(a, c, k) for a in alloys for c in coatings for k in ceramics]


def _index_to_combo(idx_a, idx_c, idx_k,
                    alloys, coatings, ceramics) -> Combo:
    return Combo(alloys[idx_a], coatings[idx_c], ceramics[idx_k])


def lhs(
    n: int,
    seed: int = 0,
    alloys: Sequence = _catalog.ALLOYS,
    coatings: Sequence = _catalog.COATINGS,
    ceramics: Sequence = _catalog.CERAMICS,
) -> list[Combo]:
    sampler = qmc.LatinHypercube(d=3, seed=seed)
    u = sampler.random(n)
    idx_a = np.floor(u[:, 0] * len(alloys)).astype(int).clip(0, len(alloys) - 1)
    idx_c = np.floor(u[:, 1] * len(coatings)).astype(int).clip(0, len(coatings) - 1)
    idx_k = np.floor(u[:, 2] * len(ceramics)).astype(int).clip(0, len(ceramics) - 1)
    return [_index_to_combo(int(a), int(c), int(k), alloys, coatings, ceramics)
            for a, c, k in zip(idx_a, idx_c, idx_k)]


def sobol(
    n: int,
    seed: int = 0,
    alloys: Sequence = _catalog.ALLOYS,
    coatings: Sequence = _catalog.COATINGS,
    ceramics: Sequence = _catalog.CERAMICS,
) -> list[Combo]:
    sampler = qmc.Sobol(d=3, scramble=True, seed=seed)
    # round n up to a power of 2 so Sobol is well-defined, then truncate.
    pow2 = 1
    while pow2 < n:
        pow2 <<= 1
    u = sampler.random_base2(int(np.log2(pow2)))[:n]
    idx_a = np.floor(u[:, 0] * len(alloys)).astype(int).clip(0, len(alloys) - 1)
    idx_c = np.floor(u[:, 1] * len(coatings)).astype(int).clip(0, len(coatings) - 1)
    idx_k = np.floor(u[:, 2] * len(ceramics)).astype(int).clip(0, len(ceramics) - 1)
    return [_index_to_combo(int(a), int(c), int(k), alloys, coatings, ceramics)
            for a, c, k in zip(idx_a, idx_c, idx_k)]


def dedupe(combos: list[Combo]) -> list[Combo]:
    seen: set[str] = set()
    out: list[Combo] = []
    for c in combos:
        if c.id not in seen:
            seen.add(c.id)
            out.append(c)
    return out
