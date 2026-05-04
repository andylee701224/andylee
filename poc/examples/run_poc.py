"""End-to-end V93K placement POC.

Pipeline: synthetic board -> randomise caps -> P1 ILP channel mapping ->
P2 SA placement -> P3 legalisation -> metrics + plots.

Run from the `poc/` directory:

    python -m examples.run_poc
"""
from __future__ import annotations

import os
import sys
import time

# Make `v93k_poc` importable when running as a script.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from v93k_poc.metrics import (
    cap_to_vdd_distance,
    drc_violations,
    site_symmetry_error,
    total_wirelength,
)
from v93k_poc.p1_mapping import solve_channel_mapping
from v93k_poc.p2_placement import simulated_annealing
from v93k_poc.p3_legalize import legalize
from v93k_poc.synthetic import make_toy_board, randomize_components
from v93k_poc.visualize import plot_board, plot_sa_history


ARTIFACTS = os.path.join(_ROOT, "artifacts")


def report(label: str, board, mapping):
    wl = total_wirelength(board, mapping)
    nv, _ = drc_violations(board)
    sym = site_symmetry_error(board)
    mean_d, max_d = cap_to_vdd_distance(board)
    print(f"  {label:<22}  "
          f"WL={wl:7.2f} mm  DRC={nv:2d}  "
          f"sym={sym:5.2f} mm  cap-VDD mean={mean_d:4.2f} max={max_d:4.2f}")


def main():
    os.makedirs(ARTIFACTS, exist_ok=True)
    print("=" * 70)
    print("V93K toy board placement POC")
    print("=" * 70)

    board = make_toy_board()
    print(f"Board: {board.width:.0f}x{board.height:.0f} mm  "
          f"anchors={len(board.anchors)}  "
          f"components={len(board.components)}  "
          f"keepouts={len(board.keepouts)}")

    randomize_components(board, seed=2026)

    # P1 -- run once on the (fixed) anchor geometry.
    t0 = time.perf_counter()
    mapping, p1_cost = solve_channel_mapping(board)
    p1_t = time.perf_counter() - t0
    print(f"\n[P1] CP-SAT channel mapping: "
          f"pairs={len(mapping)}  cost={p1_cost:.2f} mm  time={p1_t:.2f}s")

    plot_board(board, mapping=mapping,
               title=f"After randomisation + P1 mapping (HPWL={p1_cost:.2f} mm)",
               save_path=os.path.join(ARTIFACTS, "01_after_p1.png"))

    print("\nMetrics by stage:")
    report("after P1 (random caps)", board, mapping)

    # P2 SA.
    t0 = time.perf_counter()
    result = simulated_annealing(board, iters=12000, seed=42)
    p2_t = time.perf_counter() - t0
    board = result.board
    print(f"\n[P2] SA placement: "
          f"final energy={result.energy:.2f}  iters=12000  time={p2_t:.2f}s")
    plot_board(board, mapping=mapping,
               title=f"After P2 SA placement (E={result.energy:.2f})",
               save_path=os.path.join(ARTIFACTS, "02_after_p2.png"))
    plot_sa_history(result.history,
                    save_path=os.path.join(ARTIFACTS, "02_sa_energy.png"))
    report("after P2 (SA)", board, mapping)

    # P3 legalisation.
    t0 = time.perf_counter()
    info = legalize(board)
    p3_t = time.perf_counter() - t0
    print(f"\n[P3] Legalisation: "
          f"outer_iters={info['outer_iters']}  "
          f"keepout_iters={info['keepout_push_iters']}  "
          f"cap_iters={info['cap_push_iters']}  time={p3_t:.2f}s")
    plot_board(board, mapping=mapping,
               title="After P3 legalisation",
               save_path=os.path.join(ARTIFACTS, "03_after_p3.png"))
    report("after P3 (legal)", board, mapping)

    print("\nArtifacts saved under:", ARTIFACTS)
    print("=" * 70)


if __name__ == "__main__":
    main()
