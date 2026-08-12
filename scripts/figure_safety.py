#!/usr/bin/env python3
"""Small numerical and annotation-position helpers for publication figures.

Adapted from Yuan1z0825/nature-skills (Apache-2.0), nature-figure safety helpers.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def interp_monotone(target: Any, xp: Any, fp: Any) -> Any:
    """Interpolate on a strictly increasing or decreasing coordinate grid."""
    x = np.asarray(xp, dtype=float)
    values = np.asarray(fp, dtype=float)
    if x.ndim != 1 or values.ndim != 1 or x.size != values.size:
        raise ValueError("xp and fp must be one-dimensional arrays of equal length")
    if x.size < 2 or not np.all(np.isfinite(x)) or not np.all(np.isfinite(values)):
        raise ValueError("xp and fp require at least two finite values")
    differences = np.diff(x)
    if np.all(differences > 0):
        ordered_x, ordered_values = x, values
    elif np.all(differences < 0):
        ordered_x, ordered_values = x[::-1], values[::-1]
    else:
        raise ValueError("xp must be strictly monotone")
    return np.interp(target, ordered_x, ordered_values)


def label_y_above(values: Any, spread: Any | None = None, pad_fraction: float = 0.04) -> float:
    """Place a label above the maximum center plus optional uncertainty."""
    centers = np.asarray(values, dtype=float)
    if centers.size == 0 or not np.all(np.isfinite(centers)):
        raise ValueError("values must contain at least one finite value")
    upper = centers if spread is None else centers + np.asarray(spread, dtype=float)
    if not np.all(np.isfinite(upper)):
        raise ValueError("spread must contain only finite values")
    data_min = float(np.min(centers))
    data_max = float(np.max(upper))
    scale = max(data_max - data_min, abs(data_max), 1.0)
    return data_max + max(0.0, pad_fraction) * scale


__all__ = ["interp_monotone", "label_y_above"]
