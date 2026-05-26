"""Cross-axis constraint checks.

A constraint takes (combo, spec) and returns a list of `Violation` strings.
Empty list means feasible. The BO acquisition treats any non-empty list as
infeasible and gives those points -inf utility.
"""

from __future__ import annotations

from typing import Iterable

from .schemas import Combo, ProbeSpec


MAX_CTE_MISMATCH_PPM = 6.0    # alloy vs ceramic
MIN_HOLE_CLEARANCE_UM = 2.0   # hole diameter must exceed (probe body + 2*coating + clearance)
PROBE_BODY_NOMINAL_UM = 30.0  # assumed nominal probe body diameter for clearance math


def cte_mismatch(combo: Combo) -> float:
    return combo.alloy.cte_ppm_per_K - combo.ceramic.cte_ppm_per_K


def hole_clearance_um(combo: Combo, probe_body_um: float = PROBE_BODY_NOMINAL_UM) -> float:
    coated = probe_body_um + 2.0 * combo.coating.total_thickness_um
    return combo.ceramic.hole_diameter_um - coated


def deposition_compatible(combo: Combo) -> bool:
    """Reject combos where the coating deposition can't be applied on the alloy.

    e.g. ALD/PVD coatings on a machined BeCu rod are OK; electroplated Au-soft
    on top of a machined MP35N is also fine — almost everything except trying
    to LIGA a Pd alloy with the wrong bath chemistry is fine in the POC.
    """
    # Conservative: DLC over LIGA NiCo is experimental, flag but don't block.
    return True


def check(combo: Combo, spec: ProbeSpec) -> list[str]:
    violations: list[str] = []

    cte = cte_mismatch(combo)
    if abs(cte) > MAX_CTE_MISMATCH_PPM:
        violations.append(
            f"CTE mismatch {cte:+.1f} ppm/K exceeds ±{MAX_CTE_MISMATCH_PPM}"
        )

    clearance = hole_clearance_um(combo)
    if clearance < MIN_HOLE_CLEARANCE_UM:
        violations.append(
            f"Hole clearance {clearance:.1f} µm < {MIN_HOLE_CLEARANCE_UM} µm "
            f"(hole {combo.ceramic.hole_diameter_um}, coated body "
            f"{PROBE_BODY_NOMINAL_UM + 2*combo.coating.total_thickness_um:.1f})"
        )

    if combo.ceramic.hole_tolerance_um > spec.pitch_um * 0.05:
        violations.append(
            f"Hole tolerance {combo.ceramic.hole_tolerance_um} µm > 5% of "
            f"pitch ({spec.pitch_um} µm)"
        )

    if combo.coating.tip_material == "Au" and spec.pad_material in {"SnAg", "Pillar"}:
        violations.append(
            f"Au tip on {spec.pad_material} pad: Sn pickup risk"
        )

    if not deposition_compatible(combo):
        violations.append("Incompatible alloy/coating deposition stack")

    return violations


def filter_feasible(combos: Iterable[Combo], spec: ProbeSpec) -> list[Combo]:
    return [c for c in combos if not check(c, spec)]
