"""EVT / DVT / PVT / MP stage gate evaluator.

Each stage rule is a pure function `(records, spec) -> GateDecision` so it can
be tested in isolation and overridden per project.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from .schemas import GateDecision, MeasurementRecord, ProbeSpec, Stage


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _cpk(values: Sequence[float], usl: float, lsl: float | None = None) -> float:
    """One-sided Cpk against USL (the typical CRES / planarity case).

    Uses sample std with ddof=1. Returns 0 if std is zero (degenerate run).
    """
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    sigma = math.sqrt(var) if var > 0 else 1e-9
    if lsl is None:
        return (usl - mean) / (3 * sigma)
    cpu = (usl - mean) / (3 * sigma)
    cpl = (mean - lsl) / (3 * sigma)
    return min(cpu, cpl)


def _required_fields(record: MeasurementRecord, fields: Sequence[str]) -> list[str]:
    missing = [f for f in fields if getattr(record, f) is None]
    return missing


# ---------------------------------------------------------------------------
# stage rules
# ---------------------------------------------------------------------------

def evaluate_evt(records: Sequence[MeasurementRecord],
                 spec: ProbeSpec) -> GateDecision:
    """EVT: at least one combo within spec on CRES, CCC, adhesion."""
    if not records:
        return GateDecision(Stage.EVT, "FAIL", ("no records",))

    reasons: list[str] = []
    passing: list[MeasurementRecord] = []
    for r in records:
        missing = _required_fields(r, ("cres_mohm", "ccc_A",
                                        "coating_adhesion_grade"))
        if missing:
            reasons.append(f"{r.combo_id}: missing {missing}")
            continue
        within = (
            r.cres_mohm <= spec.max_cres_mohm
            and r.ccc_A >= spec.min_ccc_A
            and r.coating_adhesion_grade >= 0.7
        )
        if within:
            passing.append(r)

    if not passing:
        reasons.append("no combo within EVT spec")
        return GateDecision(Stage.EVT, "HOLD", tuple(reasons))
    return GateDecision(
        Stage.EVT, "PASS",
        (f"{len(passing)}/{len(records)} combos within spec",),
    )


def evaluate_dvt(records: Sequence[MeasurementRecord],
                 spec: ProbeSpec) -> GateDecision:
    """DVT: planarity, 100k touchdown drift, all required."""
    if not records:
        return GateDecision(Stage.DVT, "FAIL", ("no records",))

    reasons: list[str] = []
    passing = 0
    for r in records:
        missing = _required_fields(
            r, ("planarity_um", "delta_cres_pct_at_100k",
                "tip_wear_um3_per_100k"),
        )
        if missing:
            reasons.append(f"{r.combo_id}: missing {missing}")
            continue
        if (r.planarity_um <= spec.max_planarity_um
                and r.delta_cres_pct_at_100k <= 30.0):
            passing += 1
        else:
            reasons.append(
                f"{r.combo_id}: planarity={r.planarity_um}, "
                f"ΔCRES={r.delta_cres_pct_at_100k}"
            )

    if passing == 0:
        return GateDecision(Stage.DVT, "HOLD", tuple(reasons[:5]))
    return GateDecision(
        Stage.DVT, "PASS", (f"{passing}/{len(records)} combos pass DVT",),
    )


def evaluate_pvt(records: Sequence[MeasurementRecord],
                 spec: ProbeSpec,
                 cpk_target: float = 1.33,
                 min_lots: int = 3) -> GateDecision:
    """PVT: 3 lots, Cpk(CRES) >= 1.33, yield >= 99%."""
    if not records:
        return GateDecision(Stage.PVT, "FAIL", ("no records",))
    if len(records) < min_lots:
        return GateDecision(
            Stage.PVT, "HOLD",
            (f"need >= {min_lots} lot records, got {len(records)}",),
        )

    cres_values = [r.cres_mohm for r in records if r.cres_mohm is not None]
    yields = [r.yield_pct for r in records if r.yield_pct is not None]
    if not cres_values or not yields:
        return GateDecision(Stage.PVT, "HOLD", ("missing cres / yield",))

    cpk = _cpk(cres_values, usl=spec.max_cres_mohm)
    mean_yield = sum(yields) / len(yields)
    reasons = (
        f"Cpk(CRES)={cpk:.2f} (target {cpk_target})",
        f"mean yield={mean_yield:.2f}%",
    )
    if cpk >= cpk_target and mean_yield >= 99.0:
        return GateDecision(Stage.PVT, "PASS", reasons)
    return GateDecision(Stage.PVT, "HOLD", reasons)


def evaluate_mp(records: Sequence[MeasurementRecord],
                spec: ProbeSpec) -> GateDecision:
    """MP: SPC monitor. Any record with yield < 99% trips a CAPA hold."""
    if not records:
        return GateDecision(Stage.MP, "FAIL", ("no records",))
    bad = [r for r in records if r.yield_pct is not None and r.yield_pct < 99.0]
    if bad:
        return GateDecision(
            Stage.MP, "HOLD",
            (f"{len(bad)} lots below 99% yield → CAPA",),
        )
    return GateDecision(
        Stage.MP, "PASS",
        (f"{len(records)} lots within SPC",),
    )


def evaluate(stage: Stage,
             records: Sequence[MeasurementRecord],
             spec: ProbeSpec) -> GateDecision:
    return {
        Stage.EVT: evaluate_evt,
        Stage.DVT: evaluate_dvt,
        Stage.PVT: evaluate_pvt,
        Stage.MP: evaluate_mp,
    }[stage](records, spec)
