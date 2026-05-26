import numpy as np

from mems_vpc import catalog, bo
from mems_vpc.featurize import feature_matrix
from mems_vpc.schemas import Combo, MeasurementRecord, ProbeSpec, Stage


def _spec() -> ProbeSpec:
    return ProbeSpec(
        pitch_um=80.0, pad_material="Al",
        target_force_gf=2.0, target_lifetime_td=500_000,
        max_planarity_um=25.0, max_cres_mohm=80.0, min_ccc_A=1.5,
    )


def test_utility_handles_partial_record():
    spec = _spec()
    r = MeasurementRecord(combo_id="x", stage=Stage.EVT, cres_mohm=40.0)
    u = bo.utility(r, spec)
    assert isinstance(u, float)


def test_propose_returns_unseen_combos():
    spec = _spec()
    combos = list(catalog.all_combos())[:30]
    observed = [(combos[i], float(i)) for i in range(5)]
    proposals = bo.propose(observed, combos, batch_size=3)
    seen = {c.id for c, _ in observed}
    assert all(p.id not in seen for p in proposals)
    assert len(proposals) <= 3


def test_gp_fit_predict_shapes():
    combos = list(catalog.all_combos())[:8]
    X = feature_matrix(combos)
    y = np.linspace(0, 1, len(combos))
    gp = bo.fit_gp(X, y)
    mu, var = bo.predict(gp, X)
    assert mu.shape == (len(combos),)
    assert var.shape == (len(combos),)
    assert (var >= 0).all()
