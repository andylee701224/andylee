from mems_vpc.gates import (
    evaluate_evt, evaluate_dvt, evaluate_pvt, evaluate_mp, _cpk,
)
from mems_vpc.schemas import MeasurementRecord, ProbeSpec, Stage


def _spec() -> ProbeSpec:
    return ProbeSpec(
        pitch_um=80.0, pad_material="Al",
        target_force_gf=2.0, target_lifetime_td=500_000,
        max_planarity_um=25.0, max_cres_mohm=80.0, min_ccc_A=1.5,
    )


def test_evt_pass():
    spec = _spec()
    rec = MeasurementRecord(
        combo_id="x", stage=Stage.EVT,
        cres_mohm=50.0, ccc_A=2.0, coating_adhesion_grade=0.85,
    )
    d = evaluate_evt([rec], spec)
    assert d.passed()


def test_evt_hold_when_no_passing_combo():
    spec = _spec()
    rec = MeasurementRecord(
        combo_id="x", stage=Stage.EVT,
        cres_mohm=200.0, ccc_A=0.5, coating_adhesion_grade=0.5,
    )
    d = evaluate_evt([rec], spec)
    assert d.decision == "HOLD"


def test_dvt_rejects_high_drift():
    spec = _spec()
    rec = MeasurementRecord(
        combo_id="x", stage=Stage.DVT,
        planarity_um=20.0, delta_cres_pct_at_100k=80.0,
        tip_wear_um3_per_100k=500.0,
    )
    d = evaluate_dvt([rec], spec)
    assert d.decision == "HOLD"


def test_pvt_requires_three_lots():
    spec = _spec()
    rec = MeasurementRecord(
        combo_id="x", stage=Stage.PVT,
        cres_mohm=50.0, yield_pct=99.5,
    )
    d = evaluate_pvt([rec], spec)
    assert d.decision == "HOLD"


def test_pvt_pass_three_lots_low_variance():
    spec = _spec()
    recs = [
        MeasurementRecord(combo_id="x", stage=Stage.PVT,
                          cres_mohm=50.0 + i * 0.1, yield_pct=99.5)
        for i in range(3)
    ]
    d = evaluate_pvt(recs, spec)
    assert d.passed(), d.reasons


def test_mp_capa_on_low_yield():
    spec = _spec()
    recs = [
        MeasurementRecord(combo_id="x", stage=Stage.MP,
                          cres_mohm=50.0, yield_pct=98.0),
    ]
    d = evaluate_mp(recs, spec)
    assert d.decision == "HOLD"


def test_cpk_helper_monotonic():
    a = _cpk([10, 10.1, 10.2], usl=12)
    b = _cpk([10, 10.5, 11.0], usl=12)
    assert a > b
