from v93k_poc.board import SignalType
from v93k_poc.p1_mapping import solve_channel_mapping
from v93k_poc.synthetic import make_toy_board


def test_p1_assigns_all_signal_pins_with_matching_types():
    b = make_toy_board()
    mapping, cost = solve_channel_mapping(b, time_limit_s=10)
    assert cost > 0
    # Every signal pin (HS or LS) must be assigned exactly once.
    expected_pins = {a.id for a in b.anchors.values()
                     if a.role == "socket"
                     and a.signal_type in (SignalType.HIGH_SPEED, SignalType.LOW_SPEED)}
    assert set(mapping.values()) == expected_pins
    # Channel and pin must share the same signal type.
    for cid, pid in mapping.items():
        assert b.anchors[cid].signal_type == b.anchors[pid].signal_type


def test_p1_uses_distinct_channels():
    b = make_toy_board()
    mapping, _ = solve_channel_mapping(b, time_limit_s=10)
    assert len(set(mapping.keys())) == len(mapping)
