"""Numerical primitives extracted verbatim from the frozen analysis; no campaign paths."""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np

def dataset_equal_mean(x: np.ndarray, gi: np.ndarray, G: int) -> np.ndarray:
    return np.mean(np.stack([x[gi == g].mean(axis=0) for g in range(G)], axis=0), axis=0)

def dataset_equal_cov(x: np.ndarray, gi: np.ndarray, G: int) -> np.ndarray:
    """Covariance of a dataset-equal-weighted mean for x shaped (query, columns)."""
    x = np.asarray(x, dtype=float)
    if x.ndim == 1:
        x = x[:, None]
    total = np.zeros((x.shape[1], x.shape[1]), dtype=float)
    for g in range(G):
        xg = x[gi == g]
        n = xg.shape[0]
        if n < 2:
            return np.full_like(total, np.nan)
        centered = xg - xg.mean(axis=0, keepdims=True)
        total += (centered.T @ centered) / (n - 1) / n
    return total / (G * G)

def bootstrap_cell_means(
    cube: np.ndarray, gi: np.ndarray, G: int, n_boot: int, seed: int
) -> np.ndarray:
    """Dataset-stratified query-cluster bootstrap of all model x cell means."""
    rng = np.random.default_rng(seed)
    out = np.empty((n_boot, cube.shape[1], cube.shape[2]), dtype=float)
    groups = [cube[gi == g] for g in range(G)]
    for start in range(0, n_boot, 500):
        b = min(500, n_boot - start)
        block = np.zeros((b, cube.shape[1], cube.shape[2]), dtype=float)
        for xg in groups:
            n = xg.shape[0]
            counts = rng.multinomial(n, np.full(n, 1.0 / n), size=b)
            block += np.einsum("bn,nkc->bkc", counts, xg) / n / G
        out[start : start + b] = block
    return out

def _batch_equal_mean(x: np.ndarray, gi: np.ndarray, G: int) -> np.ndarray:
    """Dataset-equal mean for x shaped (batch, query, columns)."""
    return np.mean(np.stack([x[:, gi == g].mean(axis=1) for g in range(G)], axis=0), axis=0)

def _batch_equal_cov(x: np.ndarray, gi: np.ndarray, G: int) -> np.ndarray:
    """Dataset-equal covariance for x shaped (batch, query, columns)."""
    total = np.zeros((x.shape[0], x.shape[2], x.shape[2]), dtype=float)
    for g in range(G):
        xg = x[:, gi == g]
        n = xg.shape[1]
        centered = xg - xg.mean(axis=1, keepdims=True)
        total += np.einsum("bnk,bnl->bkl", centered, centered) / (n - 1) / n
    return total / (G * G)

def studentized_signflip_many(
    h: np.ndarray, gi: np.ndarray, G: int, rng: np.random.Generator, n_perm: int
) -> list[dict[str, Any]]:
    """Joint query-cluster sign flip for one or more paired contrasts."""
    h = np.asarray(h, dtype=float)
    if h.ndim == 1:
        h = h[:, None]
    num = dataset_equal_mean(h, gi, G)
    cov = dataset_equal_cov(h, gi, G)
    den = np.sqrt(np.maximum(np.diag(cov), 0.0))
    evaluable = den > 0
    obs = np.divide(np.abs(num), den, out=np.full_like(num, np.inf), where=evaluable)
    ge = np.zeros(h.shape[1], dtype=np.int64)
    for start in range(0, n_perm, 5000):
        b = min(5000, n_perm - start)
        signs = rng.choice((-1.0, 1.0), size=(b, h.shape[0], 1))
        hp = h[None, :, :] * signs
        nu = _batch_equal_mean(hp, gi, G)
        co = _batch_equal_cov(hp, gi, G)
        de = np.sqrt(np.maximum(np.diagonal(co, axis1=1, axis2=2), 0.0))
        st = np.divide(np.abs(nu), de, out=np.zeros_like(nu), where=de > 0)
        ge += (st >= obs[None, :] - 1e-12).sum(axis=0)
    out = []
    for j in range(h.shape[1]):
        if not evaluable[j]:
            status = "degenerate_zero" if abs(num[j]) < 1e-12 else "degenerate_not_evaluable"
            out.append(
                {
                    "status": status,
                    "effect_pp": round(100 * float(num[j]), 6),
                    "p_perm": 1.0,
                    "n_permutations": n_perm,
                }
            )
        else:
            out.append(
                {
                    "status": "evaluable",
                    "effect_pp": round(100 * float(num[j]), 6),
                    "statistic": round(float(obs[j]), 6),
                    "p_perm": (1 + int(ge[j])) / (n_perm + 1),
                    "n_permutations": n_perm,
                }
            )
    return out

def holm_adjust_pvalues(pvalues: Iterable[float]) -> tuple[list[float], list[int]]:
    """Return monotone Holm adjusted p-values and zero-based raw-p ranks."""
    p = np.asarray(list(pvalues), dtype=float)
    m = p.size
    order = np.argsort(p, kind="stable")
    adjusted_sorted = np.empty(m, dtype=float)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, min(1.0, float(p[idx]) * (m - rank)))
        adjusted_sorted[rank] = running
    adjusted = np.empty(m, dtype=float)
    ranks = np.empty(m, dtype=int)
    for rank, idx in enumerate(order):
        adjusted[idx] = adjusted_sorted[rank]
        ranks[idx] = rank
    return adjusted.tolist(), ranks.tolist()
