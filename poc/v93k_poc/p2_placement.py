"""P2: simulated annealing placement of decoupling caps.

Energy = w_dist  * sum |cap - target_VDD_pin|_1
        + w_overlap * cap-cap overlap area
        + w_keepout * cap-keepout overlap area
        + w_symmetry * site-to-site mirror error
        + w_bounds * out-of-board penalty
"""
from __future__ import annotations
import math
import random
from copy import deepcopy
from dataclasses import dataclass

from .board import Board


@dataclass
class SAResult:
    board: Board
    energy: float
    history: list[tuple[int, float, float, float]]   # (k, T, current_E, best_E)


def cap_to_target_distance(board: Board) -> float:
    total = 0.0
    for c in board.components.values():
        a = board.anchors[c.target_anchor_id]
        total += abs(c.x - a.x) + abs(c.y - a.y)
    return total


def cap_overlap_area(board: Board) -> float:
    comps = list(board.components.values())
    total = 0.0
    for i, a in enumerate(comps):
        for b in comps[i + 1:]:
            dx = (a.width / 2 + b.width / 2 + a.keepout + b.keepout) - abs(a.x - b.x)
            dy = (a.height / 2 + b.height / 2 + a.keepout + b.keepout) - abs(a.y - b.y)
            if dx > 0 and dy > 0:
                total += dx * dy
    return total


def keepout_overlap_area(board: Board) -> float:
    total = 0.0
    for c in board.components.values():
        for k in board.keepouts:
            dx = (c.width / 2 + k.width / 2 + c.keepout) - abs(c.x - k.x)
            dy = (c.height / 2 + k.height / 2 + c.keepout) - abs(c.y - k.y)
            if dx > 0 and dy > 0:
                total += dx * dy
    return total


def symmetry_penalty(board: Board) -> float:
    if 0 not in board.site_centers or 1 not in board.site_centers:
        return 0.0
    cx0, cy0 = board.site_centers[0]
    cx1, cy1 = board.site_centers[1]
    by_logical: dict[int, dict[int, object]] = {}
    for c in board.components.values():
        by_logical.setdefault(c.logical_index, {})[c.site] = c
    total = 0.0
    for sites in by_logical.values():
        if 0 not in sites or 1 not in sites:
            continue
        ca, cb = sites[0], sites[1]
        la = (ca.x - cx0, ca.y - cy0)
        lb = (cb.x - cx1, cb.y - cy1)
        # Mirror across vertical axis at x=0 between symmetric site centres.
        expected = (-la[0], la[1])
        total += abs(lb[0] - expected[0]) + abs(lb[1] - expected[1])
    return total


def out_of_bounds_penalty(board: Board) -> float:
    half_w = board.width / 2
    half_h = board.height / 2
    total = 0.0
    for c in board.components.values():
        ox = max(0.0, abs(c.x) + c.width / 2 - half_w)
        oy = max(0.0, abs(c.y) + c.height / 2 - half_h)
        total += ox + oy
    return total


def total_energy(board: Board, w_dist=1.0, w_overlap=15.0,
                 w_keepout=15.0, w_symmetry=2.0, w_bounds=20.0) -> float:
    return (
        w_dist * cap_to_target_distance(board)
        + w_overlap * cap_overlap_area(board)
        + w_keepout * keepout_overlap_area(board)
        + w_symmetry * symmetry_penalty(board)
        + w_bounds * out_of_bounds_penalty(board)
    )


def simulated_annealing(board: Board,
                        iters: int = 8000,
                        T_start: float = 8.0,
                        T_end: float = 0.02,
                        seed: int = 0,
                        record_every: int = 50,
                        weights: dict | None = None) -> SAResult:
    """Site-aware SA: occasionally perturb a logical pair in symmetric sync
    so the symmetry term improves more easily."""
    rng = random.Random(seed)
    weights = weights or {}
    energy_kw = {k: v for k, v in weights.items() if k.startswith("w_")}

    def E(b: Board) -> float:
        return total_energy(b, **energy_kw)

    current = deepcopy(board)
    current_E = E(current)
    best = deepcopy(current)
    best_E = current_E

    # Group components by logical_index for symmetric moves.
    by_logical: dict[int, list[str]] = {}
    for c in current.components.values():
        by_logical.setdefault(c.logical_index, []).append(c.id)

    ids = list(current.components.keys())
    history: list[tuple[int, float, float, float]] = []

    for k in range(iters):
        T = T_start * (T_end / T_start) ** (k / iters)
        sigma = T * 0.6

        # 30% of moves are symmetric pair moves; rest are single-component.
        if rng.random() < 0.30:
            li = rng.choice(list(by_logical.keys()))
            pair = by_logical[li]
            dx = rng.gauss(0, sigma)
            dy = rng.gauss(0, sigma)
            saved = []
            for cid in pair:
                c = current.components[cid]
                saved.append((cid, c.x, c.y))
                # Mirror dx between site 0 and site 1 to preserve symmetry.
                site_sign = -1.0 if c.site == 1 else 1.0
                c.x = c.x + dx * site_sign
                c.y = c.y + dy
        else:
            cid = rng.choice(ids)
            c = current.components[cid]
            saved = [(cid, c.x, c.y)]
            c.x += rng.gauss(0, sigma)
            c.y += rng.gauss(0, sigma)

        new_E = E(current)
        dE = new_E - current_E
        if dE < 0 or rng.random() < math.exp(-dE / max(T, 1e-9)):
            current_E = new_E
            if new_E < best_E:
                best_E = new_E
                best = deepcopy(current)
        else:
            for cid, ox, oy in saved:
                cc = current.components[cid]
                cc.x, cc.y = ox, oy

        if k % record_every == 0:
            history.append((k, T, current_E, best_E))

    return SAResult(board=best, energy=best_E, history=history)
