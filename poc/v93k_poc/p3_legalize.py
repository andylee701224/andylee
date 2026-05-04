"""P3: legalisation -- snap to grid and resolve residual overlaps."""
from __future__ import annotations

from .board import Board


def snap_to_grid(board: Board, grid: float | None = None) -> None:
    g = board.grid if grid is None else grid
    for c in board.components.values():
        c.x = round(c.x / g) * g
        c.y = round(c.y / g) * g


def push_apart(board: Board, max_iters: int = 200, step: float = 0.25) -> int:
    """Iteratively push overlapping components apart along the smaller axis.
    Returns the number of iterations actually run."""
    comps = list(board.components.values())
    for it in range(max_iters):
        moved = False
        for i in range(len(comps)):
            for j in range(i + 1, len(comps)):
                a, b = comps[i], comps[j]
                dx = (a.width / 2 + b.width / 2 + a.keepout + b.keepout) - abs(a.x - b.x)
                dy = (a.height / 2 + b.height / 2 + a.keepout + b.keepout) - abs(a.y - b.y)
                if dx > 0 and dy > 0:
                    moved = True
                    if dx < dy:
                        sx = step if a.x <= b.x else -step
                        a.x -= sx
                        b.x += sx
                    else:
                        sy = step if a.y <= b.y else -step
                        a.y -= sy
                        b.y += sy
        if not moved:
            return it + 1
    return max_iters


def push_out_of_keepouts(board: Board, max_iters: int = 200, step: float = 0.25) -> int:
    for it in range(max_iters):
        moved = False
        for c in board.components.values():
            for k in board.keepouts:
                dx = (c.width / 2 + k.width / 2 + c.keepout) - abs(c.x - k.x)
                dy = (c.height / 2 + k.height / 2 + c.keepout) - abs(c.y - k.y)
                if dx > 0 and dy > 0:
                    moved = True
                    # Push along the smaller-overlap axis, away from keepout centre.
                    if dx < dy:
                        c.x += step if c.x >= k.x else -step
                    else:
                        c.y += step if c.y >= k.y else -step
        if not moved:
            return it + 1
    return max_iters


def legalize(board: Board, max_outer: int = 5) -> dict:
    """Push out of keep-outs, push caps apart, snap to grid -- iterated until
    DRC-clean (snap can re-introduce overlaps, so we may need a second pass)."""
    from .metrics import drc_violations

    total_ko = total_pp = 0
    for outer in range(max_outer):
        total_ko += push_out_of_keepouts(board)
        total_pp += push_apart(board)
        snap_to_grid(board)
        if drc_violations(board)[0] == 0:
            return {
                "keepout_push_iters": total_ko,
                "cap_push_iters": total_pp,
                "outer_iters": outer + 1,
            }
    return {
        "keepout_push_iters": total_ko,
        "cap_push_iters": total_pp,
        "outer_iters": max_outer,
    }
