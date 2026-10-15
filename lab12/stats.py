"""Small statistics helpers."""
import numpy as np


def wilson(k, n, z=1.96):
    """Wilson score interval for a proportion k/n (95 % by default). Returns (low, high)."""
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    z2 = z ** 2
    d = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / d
    radicand = (p * (1.0 - p)) / n + z2 / (4.0 * (n ** 2))
    half = (z * np.sqrt(max(0.0, radicand))) / d
    low = max(0.0, center - half)
    high = min(1.0, center + half)
    return float(low), float(high)


def rate(flags):
    """{'k','n','rate','ci95'} for a boolean array."""
    flags = np.asarray(flags, bool)
    k, n = int(flags.sum()), int(flags.size)
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": k / n if n else float("nan"), "ci95": [lo, hi]}


def wasserstein1(a, b, n=200):
    """1-D Wasserstein distance between two samples (mean absolute difference of the quantile functions)."""
    q = np.linspace(0.005, 0.995, n)
    return float(np.mean(np.abs(np.quantile(a, q) - np.quantile(b, q))))
