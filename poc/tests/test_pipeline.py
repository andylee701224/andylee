"""End-to-end smoke test: random caps -> SA -> legalise should converge."""
from v93k_poc.metrics import (
    cap_to_vdd_distance,
    drc_violations,
    site_symmetry_error,
)
from v93k_poc.p2_placement import simulated_annealing
from v93k_poc.p3_legalize import legalize
from v93k_poc.synthetic import make_toy_board, randomize_components


def test_sa_then_legalize_reduces_distance_and_clears_drc():
    b = make_toy_board()
    randomize_components(b, seed=1)

    # Random scatter should be far from targets and probably violate DRC.
    _, max_before = cap_to_vdd_distance(b)
    assert max_before > 10.0

    res = simulated_annealing(b, iters=8000, seed=1)
    legalize(res.board)

    nv, _ = drc_violations(res.board)
    sym = site_symmetry_error(res.board)
    mean_d, max_d = cap_to_vdd_distance(res.board)

    assert nv == 0, "legalised layout must be DRC-clean"
    assert max_d < 6.0, f"caps should land close to VDD pins (max={max_d:.2f})"
    assert sym < 4.0, f"symmetry should be roughly preserved (err={sym:.2f})"
