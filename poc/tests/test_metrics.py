from v93k_poc.metrics import (
    cap_to_vdd_distance,
    drc_violations,
    site_symmetry_error,
    total_wirelength,
)
from v93k_poc.synthetic import make_toy_board


def test_initial_layout_is_symmetric():
    b = make_toy_board()
    assert site_symmetry_error(b) < 1e-6


def test_drc_initially_clean():
    b = make_toy_board()
    n, _ = drc_violations(b)
    assert n == 0, "factory layout should not violate DRC"


def test_total_wirelength_matches_components():
    b = make_toy_board()
    fake_mapping = {}
    wl = total_wirelength(b, fake_mapping)
    mean_d, max_d = cap_to_vdd_distance(b)
    assert wl > 0
    assert max_d <= 5.0                                        # caps stay close to VDD
    assert mean_d <= 3.5
