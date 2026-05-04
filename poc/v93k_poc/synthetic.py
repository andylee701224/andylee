"""Synthetic V93K-style toy board generator.

Layout:
    100 mm x 80 mm board, origin at centre.
    32 V93K channel pads on the top (HIGH_SPEED) and bottom (LOW_SPEED) edges.
    2 DUT sockets at sites (-15, 0) and (+15, 0); each is a 3x3 pin grid at 2.5 mm pitch:
        corners       -> HIGH_SPEED (4 pins)
        left/right    -> LOW_SPEED  (2 pins)
        top/bot mid   -> VDD        (2 pins)
        centre        -> GND        (1 pin)
    Decoupling caps: per VDD pin, 2 caps (a mirror-symmetric pair across sites).
"""
from __future__ import annotations
import random

from .board import Anchor, Board, Component, KeepoutZone, SignalType


def make_toy_board() -> Board:
    board = Board(width=100.0, height=80.0)
    board.site_centers = {0: (-15.0, 0.0), 1: (+15.0, 0.0)}

    # --- V93K channel pads -------------------------------------------------
    n_per_edge = 16
    for i in range(n_per_edge):
        x = -37.5 + i * 5.0
        top = Anchor(id=f"v93k_top_{i:02d}", x=x, y=35.0,
                     signal_type=SignalType.HIGH_SPEED, role="v93k")
        bot = Anchor(id=f"v93k_bot_{i:02d}", x=x, y=-35.0,
                     signal_type=SignalType.LOW_SPEED, role="v93k")
        board.anchors[top.id] = top
        board.anchors[bot.id] = bot

    # --- DUT sockets -------------------------------------------------------
    pitch = 2.5
    for site_idx, (cx, cy) in board.site_centers.items():
        for r in range(3):
            for c in range(3):
                px = cx + (c - 1) * pitch
                py = cy + (r - 1) * pitch
                if (r, c) == (1, 1):
                    sig = SignalType.GND
                elif (r, c) in {(0, 0), (0, 2), (2, 0), (2, 2)}:
                    sig = SignalType.HIGH_SPEED
                elif (r, c) in {(0, 1), (2, 1)}:
                    sig = SignalType.VDD
                else:                                         # (1,0) or (1,2)
                    sig = SignalType.LOW_SPEED
                aid = f"socket_s{site_idx}_r{r}_c{c}"
                board.anchors[aid] = Anchor(id=aid, x=px, y=py,
                                            signal_type=sig, role="socket",
                                            site=site_idx)
        # Socket body keep-out: just the 3x3 pin footprint, no extra clearance
        board.keepouts.append(KeepoutZone(x=cx, y=cy, width=5.0, height=5.0))

    # --- Decoupling caps (mirror-symmetric pairs) --------------------------
    # Two VDD positions per site (top-mid r=0,c=1) and (bot-mid r=2,c=1).
    # Each yields one mirror-pair of caps -> 2 pairs * 2 sites = 4 caps per site,
    # 8 caps total. logical_index pairs site-0 cap with its site-1 mirror.
    pair_idx = 0
    vdd_roles = [("vddtop", 0, 1), ("vddbot", 2, 1)]
    for role_name, rr, cc in vdd_roles:
        for k in (0, 1):
            for site_idx in (0, 1):
                target_pin_id = f"socket_s{site_idx}_r{rr}_c{cc}"
                anc = board.anchors[target_pin_id]
                # On site 0, k=0 sits to the right of pin (+1.5),
                # k=1 to the left (-1.5).  Mirror on site 1.
                base_off = 1.5 if k == 0 else -1.5
                offset_x = base_off if site_idx == 0 else -base_off
                # rr=0 lies at cy-2.5 (south edge); rr=2 at cy+2.5 (north).
                # Push the cap further from the socket centre, not into it.
                offset_y = -1.0 if rr == 0 else 1.0
                cid = f"cap_{role_name}_k{k}_s{site_idx}"
                board.components[cid] = Component(
                    id=cid, width=1.6, height=0.8, site=site_idx,
                    target_anchor_id=target_pin_id,
                    logical_index=pair_idx,
                    x=anc.x + offset_x,
                    y=anc.y + offset_y,
                )
            pair_idx += 1

    return board


def randomize_components(board: Board, seed: int = 0,
                         margin: float = 3.0) -> None:
    """Scatter caps randomly (in-place) so SA has work to do."""
    rng = random.Random(seed)
    xmin, xmax = -board.width / 2 + margin, board.width / 2 - margin
    ymin, ymax = -board.height / 2 + margin, board.height / 2 - margin
    for c in board.components.values():
        c.x = rng.uniform(xmin, xmax)
        c.y = rng.uniform(ymin, ymax)
