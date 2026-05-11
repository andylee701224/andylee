from mems_vpc import catalog
from mems_vpc.measurements import VirtualLab
from mems_vpc.schemas import Combo, ProbeSpec, Stage


def _spec() -> ProbeSpec:
    return ProbeSpec(
        pitch_um=80.0, pad_material="Al",
        target_force_gf=2.0, target_lifetime_td=500_000,
        max_planarity_um=25.0, max_cres_mohm=80.0, min_ccc_A=1.5,
    )


def test_measurement_is_deterministic():
    spec = _spec()
    lab = VirtualLab(seed=1)
    combo = Combo(catalog.ALLOYS[0], catalog.COATINGS[0], catalog.CERAMICS[0])
    r1 = lab.measure(combo, spec, Stage.EVT)
    r2 = lab.measure(combo, spec, Stage.EVT)
    assert r1.cres_mohm == r2.cres_mohm
    assert r1.ccc_A == r2.ccc_A


def test_measurement_fills_required_evt_fields():
    spec = _spec()
    lab = VirtualLab()
    combo = Combo(catalog.ALLOYS[0], catalog.COATINGS[0], catalog.CERAMICS[0])
    r = lab.measure(combo, spec, Stage.EVT)
    assert r.cres_mohm is not None
    assert r.ccc_A is not None
    assert r.coating_adhesion_grade is not None
    assert r.planarity_um is not None


def test_sn_pad_drives_higher_drift_than_al():
    spec_al = _spec()
    spec_sn = ProbeSpec(**{**spec_al.__dict__, "pad_material": "SnAg"})
    lab = VirtualLab(seed=3)
    # use a non-Au tip so the constraint doesn't reject it.
    combo = Combo(catalog.ALLOYS[0],
                  next(c for c in catalog.COATINGS if c.name == "PdCo-thick"),
                  catalog.CERAMICS[0])
    r_al = lab.measure(combo, spec_al, Stage.DVT)
    r_sn = lab.measure(combo, spec_sn, Stage.DVT)
    assert r_sn.delta_cres_pct_at_100k > r_al.delta_cres_pct_at_100k
