"""Virtual lab: analytical surrogate for (combo, spec) -> MeasurementRecord.

Replace with a real lab adapter that has the same `measure(combo, spec, stage)`
signature when bench data is wired in.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from .schemas import (
    Combo,
    MeasurementRecord,
    ProbeSpec,
    Stage,
)


# Coating-tip baseline contact resistance (mΩ) on Al pad, 5 gf, fresh tip.
_TIP_CRES_TABLE = {
    "Rh": 35.0,
    "Ru": 38.0,
    "PdCo": 50.0,
    "Au": 25.0,
    "DLC": 120.0,
    "Pd": 45.0,
    "Ni": 80.0,
}

# Adhesion grade priors per tip material (0..1, higher = stronger).
_TIP_ADHESION = {
    "Rh": 0.85,
    "Ru": 0.75,
    "PdCo": 0.9,
    "Au": 0.95,
    "DLC": 0.55,
    "Pd": 0.9,
    "Ni": 0.95,
}

# Pad-material multipliers for CRES / wear.
_PAD_FACTOR = {
    "Al": {"cres": 1.0, "wear": 1.0, "pickup": 0.6},
    "Cu": {"cres": 0.9, "wear": 1.1, "pickup": 0.3},
    "SnAg": {"cres": 1.2, "wear": 0.8, "pickup": 1.4},
    "Pillar": {"cres": 1.05, "wear": 0.9, "pickup": 1.0},
}


class VirtualLab:
    """Deterministic surrogate + gaussian noise.

    Same `combo, spec` always returns the same mean; noise is reproducible from
    a per-combo seed so re-running EVT doesn't shuffle the leaderboard.
    """

    def __init__(self, noise_scale: float = 0.05, seed: int = 0):
        self.noise_scale = noise_scale
        self._seed = seed

    # ---------------- public API ----------------

    def measure(
        self,
        combo: Combo,
        spec: ProbeSpec,
        stage: Stage,
        n_lots: int = 1,
        lot_idx: int = 0,
    ) -> MeasurementRecord:
        rng = self._rng_for(combo, stage, lot_idx)
        cres = self._cres(combo, spec, rng)
        ccc = self._ccc(combo, rng)
        planarity = self._planarity(combo, rng)
        wear = self._tip_wear(combo, spec, rng)
        delta_cres = self._delta_cres(combo, spec, rng)
        adhesion = self._adhesion(combo, rng)
        yield_pct = self._yield(combo, spec, cres, ccc, planarity, delta_cres)

        # PVT / MP report lot-averaged numbers; EVT/DVT a single fixture.
        if stage in {Stage.PVT, Stage.MP} and n_lots > 1:
            cres = float(np.mean([cres + rng.normal(0, cres * 0.02)
                                  for _ in range(n_lots)]))
            yield_pct = float(np.clip(
                yield_pct + rng.normal(0, 0.5), 0.0, 100.0
            ))

        return MeasurementRecord(
            combo_id=combo.id,
            stage=stage,
            cres_mohm=round(cres, 3),
            delta_cres_pct_at_100k=round(delta_cres, 2),
            ccc_A=round(ccc, 3),
            planarity_um=round(planarity, 2),
            tip_wear_um3_per_100k=round(wear, 1),
            coating_adhesion_grade=round(adhesion, 3),
            yield_pct=round(yield_pct, 2),
            n_lots=n_lots,
        )

    # ---------------- physics-ish surrogate ----------------

    def _rng_for(self, combo: Combo, stage: Stage,
                 lot_idx: int = 0) -> np.random.Generator:
        key = hash((combo.id, stage.value, self._seed, lot_idx)) & 0xFFFFFFFF
        return np.random.default_rng(key)

    def _cres(self, combo: Combo, spec: ProbeSpec, rng) -> float:
        tip_base = _TIP_CRES_TABLE.get(combo.coating.tip_material, 90.0)
        bulk = combo.alloy.rho_uohm_cm * 0.4   # mΩ contribution
        pad = _PAD_FACTOR.get(spec.pad_material, {"cres": 1.0})["cres"]
        # Higher hardness => slightly worse initial contact (sharp asperities OK
        # but tip flattens slowly); we model it as small +stiffness penalty.
        hard_term = 1.0 + max(0.0, (combo.coating.hardness_HV - 800) / 4000)
        mean = (tip_base + bulk) * pad * hard_term
        return max(1.0, mean * (1.0 + rng.normal(0, self.noise_scale)))

    def _ccc(self, combo: Combo, rng) -> float:
        # CCC ~ k / sqrt(rho_alloy) * geometric factor
        k = 8.0
        mean = k / math.sqrt(combo.alloy.rho_uohm_cm)
        return max(0.05, mean * (1.0 + rng.normal(0, self.noise_scale)))

    def _planarity(self, combo: Combo, rng) -> float:
        # Plate warp + 2x hole tolerance dominates planarity budget.
        mean = combo.ceramic.plate_warp_um + 2 * combo.ceramic.hole_tolerance_um
        return max(1.0, mean * (1.0 + rng.normal(0, self.noise_scale)))

    def _tip_wear(self, combo: Combo, spec: ProbeSpec, rng) -> float:
        # Archard-style: wear ∝ load * sliding / hardness
        hardness = max(50.0, combo.coating.hardness_HV)
        load_term = spec.target_force_gf
        pad_factor = _PAD_FACTOR.get(spec.pad_material, {"wear": 1.0})["wear"]
        mean = 5000.0 * load_term * pad_factor / hardness
        return max(1.0, mean * (1.0 + rng.normal(0, self.noise_scale)))

    def _delta_cres(self, combo: Combo, spec: ProbeSpec, rng) -> float:
        # Sn pickup + adhesion loss + hardness defines drift.
        pickup = _PAD_FACTOR.get(spec.pad_material, {"pickup": 1.0})["pickup"]
        stick = 1.0 - combo.coating.anti_stick_grade
        hardness_factor = 1.5 - min(1.0, combo.coating.hardness_HV / 1000)
        mean = 20.0 * pickup * (0.5 + stick) * hardness_factor
        return max(0.5, mean * (1.0 + rng.normal(0, self.noise_scale)))

    def _adhesion(self, combo: Combo, rng) -> float:
        base = _TIP_ADHESION.get(combo.coating.tip_material, 0.7)
        # Thicker coatings adhere worse (stress).
        thickness_penalty = max(0.0, combo.coating.total_thickness_um - 2.0) * 0.05
        return float(np.clip(base - thickness_penalty + rng.normal(0, 0.02),
                             0.0, 1.0))

    def _yield(self, combo: Combo, spec: ProbeSpec,
               cres: float, ccc: float, planarity: float, delta_cres: float) -> float:
        """Beta-style yield: distance-to-spec aggregated across KPIs."""
        margins = [
            (spec.max_cres_mohm - cres) / spec.max_cres_mohm,
            (ccc - spec.min_ccc_A) / max(spec.min_ccc_A, 1e-3),
            (spec.max_planarity_um - planarity) / spec.max_planarity_um,
            (30.0 - delta_cres) / 30.0,
        ]
        score = float(np.mean([max(-1.0, min(1.0, m)) for m in margins]))
        # map [-1, 1] -> [50%, 100%]
        return 50.0 + 50.0 * max(0.0, score)


def measure_batch(
    lab: VirtualLab,
    combos: list[Combo],
    spec: ProbeSpec,
    stage: Stage,
    n_lots: int = 1,
) -> list[MeasurementRecord]:
    return [lab.measure(c, spec, stage, n_lots=n_lots) for c in combos]
