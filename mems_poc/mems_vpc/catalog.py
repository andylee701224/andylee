"""Seed catalogs for R1 alloys, R2 coatings, R3 ceramics.

Numbers are illustrative defaults sourced from public datasheets / literature.
Treat as starting priors for BO — the lab adapter will overwrite them.
"""

from __future__ import annotations

from .schemas import (
    AlloyCandidate,
    CoatingCandidate,
    CoatingLayer,
    CeramicSpec,
    DepositionMethod,
    FormingMethod,
    DrillingMethod,
)


# ---------------------------------------------------------------------------
# R1 — alloys
# ---------------------------------------------------------------------------

ALLOYS: tuple[AlloyCandidate, ...] = (
    AlloyCandidate(
        name="NiCo-20",
        composition="Ni-20Co",
        E_GPa=210.0,
        sigma_y_MPa=1800.0,
        rho_uohm_cm=18.0,
        cte_ppm_per_K=12.5,
        fatigue_N_at_1pct=5e5,
        deposition_method=DepositionMethod.LIGA_ELECTROFORM,
        deposition_window={"j_A_dm2": (1.0, 5.0), "pH": (3.0, 4.5)},
    ),
    AlloyCandidate(
        name="NiMn-3",
        composition="Ni-3Mn",
        E_GPa=200.0,
        sigma_y_MPa=2200.0,
        rho_uohm_cm=32.0,
        cte_ppm_per_K=13.0,
        fatigue_N_at_1pct=4e5,
        deposition_method=DepositionMethod.LIGA_ELECTROFORM,
        deposition_window={"j_A_dm2": (0.5, 3.0)},
    ),
    AlloyCandidate(
        name="PdCo-15",
        composition="Pd-15Co",
        E_GPa=125.0,
        sigma_y_MPa=1200.0,
        rho_uohm_cm=12.0,
        cte_ppm_per_K=11.5,
        fatigue_N_at_1pct=3e5,
        deposition_method=DepositionMethod.ELECTROPLATE,
        deposition_window={"j_A_dm2": (0.3, 1.5)},
    ),
    AlloyCandidate(
        name="BeCu-C17200",
        composition="Cu-1.9Be",
        E_GPa=130.0,
        sigma_y_MPa=1300.0,
        rho_uohm_cm=7.0,
        cte_ppm_per_K=17.0,
        fatigue_N_at_1pct=2e5,
        deposition_method=DepositionMethod.MACHINING,
    ),
    AlloyCandidate(
        name="MP35N",
        composition="35Ni-35Co-20Cr-10Mo",
        E_GPa=230.0,
        sigma_y_MPa=2000.0,
        rho_uohm_cm=100.0,
        cte_ppm_per_K=13.0,
        fatigue_N_at_1pct=8e5,
        deposition_method=DepositionMethod.MACHINING,
    ),
)


# ---------------------------------------------------------------------------
# R2 — coatings
# ---------------------------------------------------------------------------

COATINGS: tuple[CoatingCandidate, ...] = (
    CoatingCandidate(
        name="Rh-tip-on-Au",
        layers=(
            CoatingLayer("Ni", 1.0),
            CoatingLayer("Au", 0.3),
            CoatingLayer("Rh", 0.8),
        ),
        hardness_HV=900.0,
        deposition_method=DepositionMethod.ELECTROPLATE,
        anti_stick_grade=0.7,
    ),
    CoatingCandidate(
        name="Ru-tip",
        layers=(
            CoatingLayer("Ni", 1.0),
            CoatingLayer("Ru", 0.6),
        ),
        hardness_HV=1000.0,
        deposition_method=DepositionMethod.PVD,
        anti_stick_grade=0.85,
    ),
    CoatingCandidate(
        name="PdCo-thick",
        layers=(
            CoatingLayer("Ni", 1.0),
            CoatingLayer("PdCo", 1.5),
        ),
        hardness_HV=600.0,
        deposition_method=DepositionMethod.ELECTROPLATE,
        anti_stick_grade=0.6,
    ),
    CoatingCandidate(
        name="Au-soft",
        layers=(
            CoatingLayer("Ni", 1.0),
            CoatingLayer("Au", 1.0),
        ),
        hardness_HV=80.0,
        deposition_method=DepositionMethod.ELECTROPLATE,
        anti_stick_grade=0.2,
    ),
    CoatingCandidate(
        name="DLC-experimental",
        layers=(
            CoatingLayer("Ti", 0.1),
            CoatingLayer("DLC", 0.5),
        ),
        hardness_HV=2200.0,
        deposition_method=DepositionMethod.PVD,
        anti_stick_grade=0.9,
    ),
)


# ---------------------------------------------------------------------------
# R3 — ceramic guide plates
# ---------------------------------------------------------------------------

CERAMICS: tuple[CeramicSpec, ...] = (
    CeramicSpec(
        material="Al2O3-995",
        E_GPa=380.0,
        cte_ppm_per_K=7.5,
        bend_strength_MPa=350.0,
        forming=FormingMethod.ISOSTATIC,
        sinter_peak_C=1600.0,
        sinter_hold_min=120.0,
        drilling=DrillingMethod.LASER_IR,
        hole_diameter_um=45.0,
        hole_tolerance_um=5.0,
        hole_wall_Ra_um=2.0,
        plate_thickness_mm=0.5,
        plate_warp_um=8.0,
    ),
    CeramicSpec(
        material="Al2O3-995",
        E_GPa=380.0,
        cte_ppm_per_K=7.5,
        bend_strength_MPa=350.0,
        forming=FormingMethod.ISOSTATIC,
        sinter_peak_C=1600.0,
        sinter_hold_min=120.0,
        drilling=DrillingMethod.LASER_UV_FS,
        hole_diameter_um=30.0,
        hole_tolerance_um=2.0,
        hole_wall_Ra_um=0.4,
        plate_thickness_mm=0.5,
        plate_warp_um=8.0,
    ),
    CeramicSpec(
        material="ZrO2-3YTZP",
        E_GPa=210.0,
        cte_ppm_per_K=10.0,
        bend_strength_MPa=1200.0,
        forming=FormingMethod.ISOSTATIC,
        sinter_peak_C=1500.0,
        sinter_hold_min=120.0,
        drilling=DrillingMethod.ULTRASONIC,
        hole_diameter_um=55.0,
        hole_tolerance_um=3.0,
        hole_wall_Ra_um=0.8,
        plate_thickness_mm=0.6,
        plate_warp_um=6.0,
    ),
    CeramicSpec(
        material="AlN",
        E_GPa=320.0,
        cte_ppm_per_K=4.5,
        bend_strength_MPa=350.0,
        forming=FormingMethod.ISOSTATIC,
        sinter_peak_C=1800.0,
        sinter_hold_min=240.0,
        drilling=DrillingMethod.LASER_UV_FS,
        hole_diameter_um=35.0,
        hole_tolerance_um=3.0,
        hole_wall_Ra_um=0.6,
        plate_thickness_mm=0.4,
        plate_warp_um=10.0,
    ),
    CeramicSpec(
        material="Si3N4",
        E_GPa=310.0,
        cte_ppm_per_K=3.2,
        bend_strength_MPa=700.0,
        forming=FormingMethod.ISOSTATIC,
        sinter_peak_C=1750.0,
        sinter_hold_min=180.0,
        drilling=DrillingMethod.LASER_UV_FS,
        hole_diameter_um=40.0,
        hole_tolerance_um=3.0,
        hole_wall_Ra_um=0.5,
        plate_thickness_mm=0.5,
        plate_warp_um=8.0,
    ),
    CeramicSpec(
        material="MACOR",
        E_GPa=67.0,
        cte_ppm_per_K=9.3,
        bend_strength_MPa=94.0,
        forming=FormingMethod.DRY_PRESS,
        sinter_peak_C=950.0,
        sinter_hold_min=60.0,
        drilling=DrillingMethod.MICRO_DRILL,
        hole_diameter_um=100.0,
        hole_tolerance_um=10.0,
        hole_wall_Ra_um=2.5,
        plate_thickness_mm=0.5,
        plate_warp_um=20.0,
    ),
)


def all_combos():
    """Cartesian product of catalogs as Combo objects.

    Cheap enough for the POC's seeded catalog (5*5*6 = 150).
    """
    from .schemas import Combo
    return tuple(
        Combo(a, c, k) for a in ALLOYS for c in COATINGS for k in CERAMICS
    )
