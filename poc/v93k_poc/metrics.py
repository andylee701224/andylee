"""Quality metrics for the toy board placement."""
from __future__ import annotations

from .board import Board


def total_wirelength(board: Board, mapping: dict[str, str]) -> float:
    """Manhattan wirelength: P1 channel<->pin + P2 cap<->target_VDD."""
    wl = 0.0
    for cid, pid in mapping.items():
        c = board.anchors[cid]
        p = board.anchors[pid]
        wl += abs(c.x - p.x) + abs(c.y - p.y)
    for comp in board.components.values():
        a = board.anchors[comp.target_anchor_id]
        wl += abs(comp.x - a.x) + abs(comp.y - a.y)
    return wl


def drc_violations(board: Board) -> tuple[int, list[tuple[str, str, float, float]]]:
    """Count overlapping component pairs (cap-cap and cap-keepout)."""
    comps = list(board.components.values())
    n = 0
    details: list[tuple[str, str, float, float]] = []
    for i, a in enumerate(comps):
        for b in comps[i + 1:]:
            dx = (a.width / 2 + b.width / 2 + a.keepout + b.keepout) - abs(a.x - b.x)
            dy = (a.height / 2 + b.height / 2 + a.keepout + b.keepout) - abs(a.y - b.y)
            if dx > 0 and dy > 0:
                n += 1
                details.append((a.id, b.id, dx, dy))
    for c in comps:
        for k_idx, k in enumerate(board.keepouts):
            dx = (c.width / 2 + k.width / 2 + c.keepout) - abs(c.x - k.x)
            dy = (c.height / 2 + k.height / 2 + c.keepout) - abs(c.y - k.y)
            if dx > 0 and dy > 0:
                n += 1
                details.append((c.id, f"keepout#{k_idx}", dx, dy))
    return n, details


def site_symmetry_error(board: Board) -> float:
    """Max abs deviation from perfect mirror symmetry (mm).
    Returns 0 when no two-site comparison is available."""
    if 0 not in board.site_centers or 1 not in board.site_centers:
        return 0.0
    cx0, cy0 = board.site_centers[0]
    cx1, cy1 = board.site_centers[1]
    by_logical: dict[int, dict[int, object]] = {}
    for c in board.components.values():
        by_logical.setdefault(c.logical_index, {})[c.site] = c
    max_err = 0.0
    for sites in by_logical.values():
        if 0 not in sites or 1 not in sites:
            continue
        ca, cb = sites[0], sites[1]
        la = (ca.x - cx0, ca.y - cy0)
        lb = (cb.x - cx1, cb.y - cy1)
        expected = (-la[0], la[1])
        err = max(abs(lb[0] - expected[0]), abs(lb[1] - expected[1]))
        max_err = max(max_err, err)
    return max_err


def cap_to_vdd_distance(board: Board) -> tuple[float, float]:
    """Mean and max cap-to-target-VDD distance (mm)."""
    if not board.components:
        return 0.0, 0.0
    dists = []
    for comp in board.components.values():
        a = board.anchors[comp.target_anchor_id]
        dists.append(abs(comp.x - a.x) + abs(comp.y - a.y))
    return sum(dists) / len(dists), max(dists)
