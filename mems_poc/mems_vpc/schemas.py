"""Core dataclasses for the MEMS VPC POC.

The three research axes (alloy, coating, ceramic) are kept as plain dataclasses
so they can be persisted to parquet/sqlite later. A `Combo` is a (alloy, coating,
ceramic) tuple that the DOE / BO layers reason over.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class DepositionMethod(str, Enum):
    LIGA_ELECTROFORM = "liga_electroform"
    DRIE_FILL = "drie_fill"
    PVD = "pvd"
    ALD = "ald"
    ELECTROPLATE = "electroplate"
    MACHINING = "machining"


class FormingMethod(str, Enum):
    DRY_PRESS = "dry_press"
    ISOSTATIC = "isostatic"
    TAPE_CAST = "tape_cast"
    SLIP_CAST = "slip_cast"
    GEL_CAST = "gel_cast"


class DrillingMethod(str, Enum):
    LASER_IR = "laser_ir"
    LASER_UV_FS = "laser_uv_fs"
    ULTRASONIC = "ultrasonic"
    MICRO_DRILL = "micro_drill"
    UECDM = "uecdm"


class Stage(str, Enum):
    EVT = "EVT"
    DVT = "DVT"
    PVT = "PVT"
    MP = "MP"


@dataclass(frozen=True)
class AlloyCandidate:
    """R1 — probe-body alloy."""
    name: str
    composition: str
    E_GPa: float
    sigma_y_MPa: float
    rho_uohm_cm: float
    cte_ppm_per_K: float
    fatigue_N_at_1pct: float
    deposition_method: DepositionMethod
    deposition_window: dict = field(default_factory=dict)


@dataclass(frozen=True)
class CoatingLayer:
    material: str
    thickness_um: float


@dataclass(frozen=True)
class CoatingCandidate:
    """R2 — probe coating stack (tip-to-base)."""
    name: str
    layers: tuple[CoatingLayer, ...]
    hardness_HV: float
    deposition_method: DepositionMethod
    anti_stick_grade: float  # 0..1, 1 = no Sn pickup
    deposition_window: dict = field(default_factory=dict)

    @property
    def total_thickness_um(self) -> float:
        return sum(layer.thickness_um for layer in self.layers)

    @property
    def tip_material(self) -> str:
        return self.layers[-1].material if self.layers else ""


@dataclass(frozen=True)
class CeramicSpec:
    """R3 — ceramic guide plate."""
    material: str
    E_GPa: float
    cte_ppm_per_K: float
    bend_strength_MPa: float
    forming: FormingMethod
    sinter_peak_C: float
    sinter_hold_min: float
    drilling: DrillingMethod
    hole_diameter_um: float
    hole_tolerance_um: float
    hole_wall_Ra_um: float
    plate_thickness_mm: float
    plate_warp_um: float


@dataclass(frozen=True)
class ProbeSpec:
    """Input spec from the test-program / package team.

    Drives DOE bounds and gate criteria.
    """
    pitch_um: float
    pad_material: str            # "Al", "Cu", "SnAg", "Pillar"
    target_force_gf: float
    target_lifetime_td: int
    max_planarity_um: float
    max_cres_mohm: float
    min_ccc_A: float
    operating_temp_C: tuple[float, float] = (-40.0, 150.0)


@dataclass(frozen=True)
class Combo:
    """One candidate point in the (alloy x coating x ceramic) space."""
    alloy: AlloyCandidate
    coating: CoatingCandidate
    ceramic: CeramicSpec

    @property
    def id(self) -> str:
        return f"{self.alloy.name}|{self.coating.name}|{self.ceramic.material}-{self.ceramic.drilling.value}"


@dataclass
class MeasurementRecord:
    """Output of a single (combo, fixture) measurement event.

    Mutable on purpose — lab adapters fill fields incrementally.
    """
    combo_id: str
    stage: Stage
    cres_mohm: Optional[float] = None
    delta_cres_pct_at_100k: Optional[float] = None
    ccc_A: Optional[float] = None
    planarity_um: Optional[float] = None
    tip_wear_um3_per_100k: Optional[float] = None
    coating_adhesion_grade: Optional[float] = None
    yield_pct: Optional[float] = None
    n_lots: int = 0
    notes: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["stage"] = self.stage.value
        return d


@dataclass(frozen=True)
class GateDecision:
    stage: Stage
    decision: str   # "PASS" | "HOLD" | "FAIL"
    reasons: tuple[str, ...]

    def passed(self) -> bool:
        return self.decision == "PASS"
