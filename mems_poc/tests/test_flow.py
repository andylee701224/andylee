from mems_vpc import flow
from mems_vpc.measurements import VirtualLab
from mems_vpc.schemas import ProbeSpec, Stage


def _spec() -> ProbeSpec:
    return ProbeSpec(
        pitch_um=80.0,
        pad_material="Al",
        target_force_gf=2.0,
        target_lifetime_td=500_000,
        max_planarity_um=30.0,
        max_cres_mohm=120.0,
        min_ccc_A=1.0,
    )


def test_evt_runs_and_produces_records():
    spec = _spec()
    lab = VirtualLab(seed=0)
    ledger = flow.StageLedger()
    report = flow.run_evt(spec, lab, ledger,
                          initial_doe=8, bo_rounds=1, bo_batch=2)
    assert report.stage == Stage.EVT
    assert len(ledger.records(Stage.EVT)) >= 8


def test_full_flow_smokes():
    spec = _spec()
    ledger, reports = flow.run_full_flow(spec, seed=0)
    stages_run = [r.stage for r in reports]
    assert Stage.EVT in stages_run
    # at least EVT must produce records
    assert len(ledger.records(Stage.EVT)) > 0
    # every report has a decision
    assert all(r.decision.decision in {"PASS", "HOLD", "FAIL"} for r in reports)


def test_promoted_ids_carry_forward():
    spec = _spec()
    lab = VirtualLab(seed=1)
    ledger = flow.StageLedger()
    evt = flow.run_evt(spec, lab, ledger, initial_doe=10, bo_rounds=1, bo_batch=3)
    if evt.promoted:
        dvt = flow.run_dvt(spec, lab, ledger, evt.promoted)
        # DVT measurement set size == promoted set size
        assert len(ledger.records(Stage.DVT)) == len(evt.promoted)
