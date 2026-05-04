"""Data model for the V93K toy placement POC.

A `Board` holds three things:
    - `anchors`   : fixed-position pins (V93K channel landing pads + DUT socket pins)
    - `components`: placeable components (decoupling caps in this POC)
    - `keepouts`  : forbidden zones (the socket bodies)

Coordinates are in millimetres, origin at board centre.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class SignalType(Enum):
    HIGH_SPEED = "HS"
    LOW_SPEED = "LS"
    VDD = "VDD"
    GND = "GND"


@dataclass(frozen=True)
class Anchor:
    id: str
    x: float
    y: float
    signal_type: SignalType
    role: str            # "v93k" or "socket"
    site: int = -1       # -1 if not site-bound


@dataclass
class Component:
    id: str
    width: float
    height: float
    site: int
    target_anchor_id: str   # the VDD anchor this cap decouples
    logical_index: int      # pairs caps that should be mirror-symmetric across sites
    x: float = 0.0
    y: float = 0.0
    rotation: int = 0       # 0 or 90
    keepout: float = 0.3


@dataclass(frozen=True)
class KeepoutZone:
    """Axis-aligned rectangle (centre + size) that components must avoid."""
    x: float
    y: float
    width: float
    height: float


@dataclass
class Board:
    width: float
    height: float
    anchors: dict[str, Anchor] = field(default_factory=dict)
    components: dict[str, Component] = field(default_factory=dict)
    keepouts: list[KeepoutZone] = field(default_factory=list)
    site_centers: dict[int, tuple[float, float]] = field(default_factory=dict)
    grid: float = 0.25
