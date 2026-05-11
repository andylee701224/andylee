from mems_vpc import doe


def test_full_factorial_cardinality():
    combos = doe.full_factorial()
    assert len(combos) > 0
    assert len({c.id for c in combos}) == len(combos)


def test_lhs_returns_n():
    combos = doe.lhs(n=20, seed=42)
    assert len(combos) == 20


def test_sobol_returns_n():
    combos = doe.sobol(n=16, seed=7)
    assert len(combos) == 16


def test_dedupe():
    combos = doe.full_factorial()
    dup = combos + combos[:5]
    out = doe.dedupe(dup)
    assert len(out) == len(combos)
