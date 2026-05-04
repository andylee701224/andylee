from v93k_poc.board import SignalType
from v93k_poc.synthetic import make_toy_board, randomize_components


def test_board_dimensions():
    b = make_toy_board()
    assert b.width == 100.0
    assert b.height == 80.0
    assert b.site_centers == {0: (-15.0, 0.0), 1: (15.0, 0.0)}


def test_anchor_counts_and_signal_split():
    b = make_toy_board()
    v93k = [a for a in b.anchors.values() if a.role == "v93k"]
    socket = [a for a in b.anchors.values() if a.role == "socket"]
    assert len(v93k) == 32
    assert len(socket) == 18                                   # 2 sites x 9 pins

    socket_by_sig = {s: 0 for s in SignalType}
    for a in socket:
        socket_by_sig[a.signal_type] += 1
    assert socket_by_sig[SignalType.HIGH_SPEED] == 8           # 4 corners x 2 sites
    assert socket_by_sig[SignalType.LOW_SPEED] == 4
    assert socket_by_sig[SignalType.VDD] == 4
    assert socket_by_sig[SignalType.GND] == 2


def test_component_count_and_targets():
    b = make_toy_board()
    assert len(b.components) == 8                              # 2 vdd_pos x 2 caps x 2 sites
    for c in b.components.values():
        assert c.target_anchor_id in b.anchors
        assert b.anchors[c.target_anchor_id].signal_type == SignalType.VDD


def test_logical_index_pairs_sites():
    b = make_toy_board()
    by_li = {}
    for c in b.components.values():
        by_li.setdefault(c.logical_index, set()).add(c.site)
    for sites in by_li.values():
        assert sites == {0, 1}, "every logical index should appear in both sites"


def test_randomize_keeps_components_inside_board():
    b = make_toy_board()
    randomize_components(b, seed=7, margin=2.0)
    for c in b.components.values():
        assert -b.width / 2 + 1 < c.x < b.width / 2 - 1
        assert -b.height / 2 + 1 < c.y < b.height / 2 - 1
