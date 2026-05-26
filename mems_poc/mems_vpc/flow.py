"""End-to-end EVT → DVT → PVT → MP closed-loop runner.

This is the orchestration layer that ties DOE / lab / constraints / BO / gates
together. Stateful via the `StageLedger`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import (
    Combo,
    GateDecision,
    MeasurementRecord,
    ProbeSpec,
    Stage,
)
from .measurements import VirtualLab
from . import bo as _bo
from . import constraints as _constraints
from . import doe as _doe
from . import gates as _gates


@dataclass
class StageLedger:
    """All measurements, indexed by stage. Survives across stage transitions."""
    by_stage: dict[Stage, list[MeasurementRecord]] = field(default_factory=dict)

    def add(self, record: MeasurementRecord) -> None:
        self.by_stage.setdefault(record.stage, []).append(record)

    def records(self, stage: Stage) -> list[MeasurementRecord]:
        return list(self.by_stage.get(stage, []))

    def combos(self, stage: Stage) -> list[str]:
        return [r.combo_id for r in self.records(stage)]

    def all_records(self) -> list[MeasurementRecord]:
        return [r for rs in self.by_stage.values() for r in rs]


@dataclass
class StageReport:
    stage: Stage
    decision: GateDecision
    n_evaluated: int
    n_passing: int
    promoted: tuple[str, ...]


# ---------------------------------------------------------------------------
# Stage runners
# ---------------------------------------------------------------------------

def _utility_pairs(records: list[MeasurementRecord],
                   combos_by_id: dict[str, Combo],
                   spec: ProbeSpec) -> list[tuple[Combo, float]]:
    out: list[tuple[Combo, float]] = []
    for r in records:
        combo = combos_by_id.get(r.combo_id)
        if combo is None:
            continue
        out.append((combo, _bo.utility(r, spec)))
    return out


def run_evt(
    spec: ProbeSpec,
    lab: VirtualLab,
    ledger: StageLedger,
    *,
    initial_doe: int = 16,
    bo_rounds: int = 3,
    bo_batch: int = 4,
    seed: int = 0,
) -> StageReport:
    candidates = _constraints.filter_feasible(_doe.full_factorial(), spec)
    if not candidates:
        decision = GateDecision(Stage.EVT, "FAIL",
                                ("no feasible combos after constraints",))
        return StageReport(Stage.EVT, decision, 0, 0, ())

    combos_by_id = {c.id: c for c in candidates}

    # Seed DOE: Sobol over feasible set.
    seed_idx = _doe.dedupe(_doe.sobol(min(initial_doe, len(candidates)),
                                       seed=seed))
    seed_idx = [c for c in seed_idx if c.id in combos_by_id][:initial_doe]
    # Fill up with deterministic head of catalog if Sobol produced too few.
    if len(seed_idx) < initial_doe:
        for c in candidates:
            if c.id not in {x.id for x in seed_idx}:
                seed_idx.append(c)
            if len(seed_idx) >= initial_doe:
                break

    for combo in seed_idx:
        ledger.add(lab.measure(combo, spec, Stage.EVT))

    # BO rounds.
    for _ in range(bo_rounds):
        observed = _utility_pairs(ledger.records(Stage.EVT), combos_by_id, spec)
        proposals = _bo.propose(observed, candidates, batch_size=bo_batch)
        if not proposals:
            break
        for combo in proposals:
            ledger.add(lab.measure(combo, spec, Stage.EVT))

    records = ledger.records(Stage.EVT)
    decision = _gates.evaluate(Stage.EVT, records, spec)

    # Promote: top-3 by utility that are also within EVT spec.
    ranked = sorted(_utility_pairs(records, combos_by_id, spec),
                    key=lambda p: -p[1])
    promoted: list[str] = []
    for combo, _u in ranked:
        # Apply gate criteria again to the single record (most recent).
        latest = [r for r in records if r.combo_id == combo.id][-1]
        if (latest.cres_mohm is not None and latest.cres_mohm <= spec.max_cres_mohm
                and latest.ccc_A is not None and latest.ccc_A >= spec.min_ccc_A
                and latest.coating_adhesion_grade is not None
                and latest.coating_adhesion_grade >= 0.7):
            promoted.append(combo.id)
        if len(promoted) >= 3:
            break

    return StageReport(Stage.EVT, decision, len(records),
                       len([r for r in records if r.combo_id in promoted]),
                       tuple(promoted))


def run_dvt(
    spec: ProbeSpec,
    lab: VirtualLab,
    ledger: StageLedger,
    promoted_ids: tuple[str, ...],
) -> StageReport:
    if not promoted_ids:
        decision = GateDecision(Stage.DVT, "FAIL", ("no promoted combos",))
        return StageReport(Stage.DVT, decision, 0, 0, ())

    catalog_combos = {c.id: c for c in _doe.full_factorial()}
    combos = [catalog_combos[i] for i in promoted_ids if i in catalog_combos]
    for combo in combos:
        ledger.add(lab.measure(combo, spec, Stage.DVT))

    records = ledger.records(Stage.DVT)
    decision = _gates.evaluate(Stage.DVT, records, spec)

    passing: list[str] = []
    for r in records:
        if (r.planarity_um is not None and r.planarity_um <= spec.max_planarity_um
                and r.delta_cres_pct_at_100k is not None
                and r.delta_cres_pct_at_100k <= 30.0):
            passing.append(r.combo_id)

    return StageReport(Stage.DVT, decision, len(records),
                       len(passing), tuple(passing[:2]))


def run_pvt(
    spec: ProbeSpec,
    lab: VirtualLab,
    ledger: StageLedger,
    locked_id: str,
    n_lots: int = 3,
) -> StageReport:
    catalog_combos = {c.id: c for c in _doe.full_factorial()}
    if locked_id not in catalog_combos:
        return StageReport(Stage.PVT,
                           GateDecision(Stage.PVT, "FAIL",
                                        (f"unknown combo {locked_id}",)),
                           0, 0, ())
    combo = catalog_combos[locked_id]
    for lot_idx in range(n_lots):
        ledger.add(lab.measure(combo, spec, Stage.PVT, n_lots=1,
                               lot_idx=lot_idx))

    records = ledger.records(Stage.PVT)
    decision = _gates.evaluate(Stage.PVT, records, spec)
    promoted = (locked_id,) if decision.passed() else ()
    return StageReport(Stage.PVT, decision, len(records),
                       len(records) if decision.passed() else 0, promoted)


def run_mp(
    spec: ProbeSpec,
    lab: VirtualLab,
    ledger: StageLedger,
    locked_id: str,
    n_lots: int = 6,
) -> StageReport:
    catalog_combos = {c.id: c for c in _doe.full_factorial()}
    if locked_id not in catalog_combos:
        return StageReport(Stage.MP,
                           GateDecision(Stage.MP, "FAIL",
                                        (f"unknown combo {locked_id}",)),
                           0, 0, ())
    combo = catalog_combos[locked_id]
    for lot_idx in range(n_lots):
        ledger.add(lab.measure(combo, spec, Stage.MP, n_lots=1,
                               lot_idx=lot_idx))

    records = ledger.records(Stage.MP)
    decision = _gates.evaluate(Stage.MP, records, spec)
    return StageReport(Stage.MP, decision, len(records),
                       sum(1 for r in records
                           if r.yield_pct is not None and r.yield_pct >= 99.0),
                       (locked_id,))


# ---------------------------------------------------------------------------
# Composite runner
# ---------------------------------------------------------------------------

def run_full_flow(
    spec: ProbeSpec,
    *,
    lab: VirtualLab | None = None,
    seed: int = 0,
) -> tuple[StageLedger, list[StageReport]]:
    lab = lab or VirtualLab(seed=seed)
    ledger = StageLedger()
    reports: list[StageReport] = []

    evt = run_evt(spec, lab, ledger, seed=seed)
    reports.append(evt)
    if not evt.decision.passed() or not evt.promoted:
        return ledger, reports

    dvt = run_dvt(spec, lab, ledger, evt.promoted)
    reports.append(dvt)
    if not dvt.decision.passed() or not dvt.promoted:
        return ledger, reports

    locked = dvt.promoted[0]
    pvt = run_pvt(spec, lab, ledger, locked)
    reports.append(pvt)
    if not pvt.decision.passed():
        return ledger, reports

    mp = run_mp(spec, lab, ledger, locked)
    reports.append(mp)
    return ledger, reports
