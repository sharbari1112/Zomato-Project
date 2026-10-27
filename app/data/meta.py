"""Catalog-derived metadata for UI dropdowns (`GET /meta`)."""

from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

from app.data.transform import compute_budget_cutoffs


def _nonempty_strings(series: pd.Series) -> list[str]:
    values: list[str] = []
    for value in series.dropna().tolist():
        text = str(value).strip()
        if text:
            values.append(text)
    return values


def _cuisine_parts(value: Any) -> list[str]:
    """Split a catalog cuisines cell into individual cuisine names.

    Parquet often loads list columns as numpy ndarrays; those are not
    ``list`` instances, so ``str(array)`` must not become a dropdown option.
    """
    if value is None:
        return []
    try:
        if pd.isna(value):
            return []
    except (TypeError, ValueError):
        pass
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    try:
        return [str(part).strip() for part in list(value) if str(part).strip()]
    except TypeError:
        text = str(value).strip()
        return [text] if text else []


def _cuisine_counts(series: pd.Series) -> Counter[str]:
    counts: Counter[str] = Counter()
    for value in series.dropna().tolist():
        for text in _cuisine_parts(value):
            counts[text] += 1
    return counts


def build_catalog_meta(
    catalog: pd.DataFrame,
    *,
    location_limit: int = 50,
    cuisine_limit: int = 40,
) -> dict[str, Any]:
    """Distinct cities/locations, sample cuisines, and budget cutoffs from the catalog."""
    cities = sorted(set(_nonempty_strings(catalog["city"]))) if "city" in catalog.columns else []
    location_counts = Counter(_nonempty_strings(catalog["location"])) if "location" in catalog.columns else Counter()
    locations = [name for name, _ in location_counts.most_common(location_limit)]
    cuisine_counts = _cuisine_counts(catalog["cuisines"]) if "cuisines" in catalog.columns else Counter()
    cuisines = [name for name, _ in cuisine_counts.most_common(cuisine_limit)]

    cutoffs = compute_budget_cutoffs(
        catalog["cost"] if "cost" in catalog.columns else pd.Series(dtype=float)
    )
    budget_cutoffs = None
    if cutoffs is not None:
        budget_cutoffs = {
            "low_max": float(cutoffs[0]),
            "medium_max": float(cutoffs[1]),
        }

    return {
        "cities": cities,
        "locations": locations,
        "cuisines": cuisines,
        "budget_cutoffs": budget_cutoffs,
    }
