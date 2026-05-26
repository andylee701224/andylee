"""Numeric featurization for combos so the BO surrogate can regress on them."""

from __future__ import annotations

import numpy as np

from .schemas import Combo


FEATURE_NAMES = (
    "E_GPa",
    "sigma_y_MPa",
    "rho_uohm_cm",
    "alloy_cte",
    "coat_hardness_HV",
    "coat_thickness_um",
    "anti_stick",
    "ceramic_E",
    "ceramic_cte",
    "hole_tol_um",
    "hole_Ra_um",
    "plate_warp_um",
)


def feature_vector(combo: Combo) -> np.ndarray:
    return np.array([
        combo.alloy.E_GPa,
        combo.alloy.sigma_y_MPa,
        combo.alloy.rho_uohm_cm,
        combo.alloy.cte_ppm_per_K,
        combo.coating.hardness_HV,
        combo.coating.total_thickness_um,
        combo.coating.anti_stick_grade,
        combo.ceramic.E_GPa,
        combo.ceramic.cte_ppm_per_K,
        combo.ceramic.hole_tolerance_um,
        combo.ceramic.hole_wall_Ra_um,
        combo.ceramic.plate_warp_um,
    ], dtype=float)


def feature_matrix(combos: list[Combo]) -> np.ndarray:
    return np.vstack([feature_vector(c) for c in combos])


def standardize(X: np.ndarray, ref: np.ndarray | None = None
                ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (X_std, mean, std). If ref is given, use its mean/std instead."""
    base = ref if ref is not None else X
    mu = base.mean(axis=0)
    sd = base.std(axis=0)
    sd = np.where(sd < 1e-9, 1.0, sd)
    return (X - mu) / sd, mu, sd
