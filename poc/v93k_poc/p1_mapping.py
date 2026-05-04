"""P1: V93K channel <-> DUT socket pin assignment via CP-SAT.

Modelled as an assignment problem: pick a perfect matching from V93K channels
to socket pins of the same SignalType (HS/LS only; VDD/GND are handled later
by P2 placement of decoupling caps).  Objective = sum of Manhattan distances.
"""
from __future__ import annotations

from ortools.sat.python import cp_model

from .board import Board, SignalType


_INT_SCALE = 100  # mm -> 0.01 mm precision for integer objective


def solve_channel_mapping(board: Board, time_limit_s: float = 5.0):
    channels = [a for a in board.anchors.values() if a.role == "v93k"]
    pins = [a for a in board.anchors.values()
            if a.role == "socket"
            and a.signal_type in (SignalType.HIGH_SPEED, SignalType.LOW_SPEED)]

    model = cp_model.CpModel()
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    for c in channels:
        for p in pins:
            if c.signal_type != p.signal_type:
                continue
            x[(c.id, p.id)] = model.NewBoolVar(f"x_{c.id}__{p.id}")

    # Each socket pin gets exactly one channel.
    for p in pins:
        candidates = [x[(c.id, p.id)] for c in channels if (c.id, p.id) in x]
        if not candidates:
            raise RuntimeError(f"No matching V93K channel for pin {p.id}")
        model.Add(sum(candidates) == 1)

    # Each channel is used at most once.
    for c in channels:
        candidates = [x[(c.id, p.id)] for p in pins if (c.id, p.id) in x]
        if candidates:
            model.Add(sum(candidates) <= 1)

    obj_terms = []
    for (cid, pid), var in x.items():
        c = board.anchors[cid]
        p = board.anchors[pid]
        d = int(round((abs(c.x - p.x) + abs(c.y - p.y)) * _INT_SCALE))
        obj_terms.append(d * var)
    model.Minimize(sum(obj_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"CP-SAT failed with status {status}")

    mapping = {cid: pid for (cid, pid), var in x.items()
               if solver.Value(var) == 1}
    return mapping, solver.ObjectiveValue() / _INT_SCALE
