"""Small Gaussian-process surrogate + Expected-Improvement acquisition.

Hand-rolled GP (RBF + jitter) so we don't pull in scikit-learn for ~30 lines
of linear algebra. The discrete (alloy x coating x ceramic) catalog is small
enough that we score the whole catalog every iteration and pick the top-k.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.stats import norm

from .schemas import Combo, MeasurementRecord, ProbeSpec
from .featurize import feature_matrix, standardize


def utility(record: MeasurementRecord, spec: ProbeSpec) -> float:
    """Single scalar 'goodness' used to drive BO. Higher is better.

    Weighted: CRES (lower better), CCC (higher), planarity (lower), drift (lower),
    yield (higher). Each term margin-normalised so they're comparable.
    """
    parts = []
    if record.cres_mohm is not None:
        parts.append((spec.max_cres_mohm - record.cres_mohm) / spec.max_cres_mohm)
    if record.ccc_A is not None:
        parts.append((record.ccc_A - spec.min_ccc_A) / max(spec.min_ccc_A, 1e-3))
    if record.planarity_um is not None:
        parts.append((spec.max_planarity_um - record.planarity_um)
                     / spec.max_planarity_um)
    if record.delta_cres_pct_at_100k is not None:
        parts.append((30.0 - record.delta_cres_pct_at_100k) / 30.0)
    if record.yield_pct is not None:
        parts.append((record.yield_pct - 90.0) / 10.0)
    if not parts:
        return 0.0
    return float(np.mean(parts))


# ---------------------------------------------------------------------------
# Tiny GP
# ---------------------------------------------------------------------------

@dataclass
class GPState:
    X_std: np.ndarray
    mu_x: np.ndarray
    sd_x: np.ndarray
    y: np.ndarray
    y_mean: float
    length_scale: float
    cho: tuple
    alpha: np.ndarray


def _rbf(A: np.ndarray, B: np.ndarray, length_scale: float) -> np.ndarray:
    d2 = np.sum(A * A, axis=1)[:, None] + np.sum(B * B, axis=1)[None, :] \
         - 2.0 * A @ B.T
    return np.exp(-0.5 * d2 / (length_scale ** 2))


def fit_gp(X: np.ndarray, y: np.ndarray,
           length_scale: float = 1.5,
           jitter: float = 1e-3) -> GPState:
    X_std, mu_x, sd_x = standardize(X)
    y_mean = float(np.mean(y))
    y0 = y - y_mean
    K = _rbf(X_std, X_std, length_scale) + jitter * np.eye(len(X_std))
    cho = cho_factor(K, lower=True)
    alpha = cho_solve(cho, y0)
    return GPState(X_std=X_std, mu_x=mu_x, sd_x=sd_x, y=y, y_mean=y_mean,
                   length_scale=length_scale, cho=cho, alpha=alpha)


def predict(gp: GPState, X_query: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    Xq_std = (X_query - gp.mu_x) / gp.sd_x
    K_qx = _rbf(Xq_std, gp.X_std, gp.length_scale)
    mu = K_qx @ gp.alpha + gp.y_mean
    v = cho_solve(gp.cho, K_qx.T)
    var = 1.0 - np.einsum("ij,ji->i", K_qx, v)
    var = np.clip(var, 1e-9, None)
    return mu, var


def expected_improvement(mu: np.ndarray, var: np.ndarray,
                         y_best: float, xi: float = 0.01) -> np.ndarray:
    sigma = np.sqrt(var)
    imp = mu - y_best - xi
    z = imp / sigma
    return imp * norm.cdf(z) + sigma * norm.pdf(z)


# ---------------------------------------------------------------------------
# Acquisition
# ---------------------------------------------------------------------------

def propose(
    observed: list[tuple[Combo, float]],
    candidates: list[Combo],
    batch_size: int,
    length_scale: float = 1.5,
) -> list[Combo]:
    """Pick `batch_size` candidates with highest EI."""
    seen_ids = {c.id for c, _ in observed}
    pool = [c for c in candidates if c.id not in seen_ids]
    if not pool:
        return []

    if len(observed) < 2:
        # Cold start: just return the first `batch_size` candidates by ID.
        return pool[:batch_size]

    X_obs = feature_matrix([c for c, _ in observed])
    y_obs = np.array([u for _, u in observed])
    gp = fit_gp(X_obs, y_obs, length_scale=length_scale)

    X_q = feature_matrix(pool)
    mu, var = predict(gp, X_q)
    ei = expected_improvement(mu, var, y_best=float(np.max(y_obs)))

    order = np.argsort(-ei)
    chosen: list[Combo] = []
    seen_ids_run = set()
    for idx in order:
        c = pool[int(idx)]
        if c.id in seen_ids_run:
            continue
        chosen.append(c)
        seen_ids_run.add(c.id)
        if len(chosen) >= batch_size:
            break
    return chosen
