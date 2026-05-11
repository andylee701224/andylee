from mems_vpc import catalog, constraints
from mems_vpc.schemas import Combo, ProbeSpec


def _default_spec(pad: str = "Al") -> ProbeSpec:
    return ProbeSpec(
        pitch_um=80.0,
        pad_material=pad,
        target_force_gf=2.0,
        target_lifetime_td=500_000,
        max_planarity_um=25.0,
        max_cres_mohm=80.0,
        min_ccc_A=1.5,
    )


def test_filter_returns_subset():
    spec = _default_spec()
    combos = list(catalog.all_combos())
    feasible = constraints.filter_feasible(combos, spec)
    assert 0 < len(feasible) <= len(combos)


def test_au_tip_on_snag_is_rejected():
    spec = _default_spec(pad="SnAg")
    au = next(c for c in catalog.COATINGS if c.name == "Au-soft")
    alloy = catalog.ALLOYS[0]
    ceramic = catalog.CERAMICS[0]
    combo = Combo(alloy, au, ceramic)
    violations = constraints.check(combo, spec)
    assert any("Sn pickup" in v for v in violations)


def test_cte_mismatch_flagged():
    spec = _default_spec()
    # BeCu has CTE 17, AlN has CTE 4.5 -> mismatch 12.5 > 6
    becu = next(a for a in catalog.ALLOYS if a.name == "BeCu-C17200")
    aln = next(c for c in catalog.CERAMICS if c.material == "AlN")
    coat = catalog.COATINGS[0]
    combo = Combo(becu, coat, aln)
    violations = constraints.check(combo, spec)
    assert any("CTE mismatch" in v for v in violations)
