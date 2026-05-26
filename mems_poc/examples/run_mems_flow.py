"""End-to-end demo: EVT -> DVT -> PVT -> MP on a synthetic probe spec.

Run:
    python -m examples.run_mems_flow

Writes nothing to disk in the POC; prints a stage-by-stage report.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python examples/run_mems_flow.py` from anywhere.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mems_vpc import flow
from mems_vpc.bo import utility
from mems_vpc.measurements import VirtualLab
from mems_vpc.schemas import ProbeSpec, Stage


def main() -> None:
    spec = ProbeSpec(
        pitch_um=80.0,
        pad_material="Al",
        target_force_gf=2.0,
        target_lifetime_td=500_000,
        max_planarity_um=30.0,
        max_cres_mohm=120.0,
        min_ccc_A=1.0,
    )

    lab = VirtualLab(seed=42)
    ledger, reports = flow.run_full_flow(spec, lab=lab, seed=42)

    print(f"Spec: pitch={spec.pitch_um}um pad={spec.pad_material} "
          f"max_CRES={spec.max_cres_mohm}mΩ min_CCC={spec.min_ccc_A}A")
    print("=" * 78)

    for report in reports:
        d = report.decision
        print(f"[{report.stage.value}] decision={d.decision} "
              f"evaluated={report.n_evaluated} "
              f"passing={report.n_passing} "
              f"promoted={list(report.promoted)}")
        for reason in d.reasons:
            print(f"    - {reason}")

    # Top-5 EVT leaderboard by utility.
    evt_records = ledger.records(Stage.EVT)
    if evt_records:
        ranked = sorted(evt_records,
                        key=lambda r: -utility(r, spec))[:5]
        print()
        print("Top-5 EVT candidates (highest utility):")
        for r in ranked:
            print(f"  {r.combo_id:<60s} "
                  f"CRES={r.cres_mohm}mΩ CCC={r.ccc_A}A "
                  f"planarity={r.planarity_um}µm "
                  f"u={utility(r, spec):.3f}")


if __name__ == "__main__":
    main()
