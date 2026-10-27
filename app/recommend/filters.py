"""Deterministic shortlist from catalog facts. No LLM, no network."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd

from app.config import SHORTLIST_SIZE

CANDIDATE_FIELDS = (
    "id",
    "name",
    "location",
    "city",
    "cuisines",
    "rating",
    "cost",
    "budget_band",
    "extra",
)


@dataclass(frozen=True)
class Preferences:
    """Structured search constraints. `notes` is ignored here on purpose."""

    location: str
    budget: str
    cuisine: str
    min_rating: float
    notes: str | None = None


def _as_preferences(preferences: Preferences | Mapping[str, Any]) -> Preferences:
    if isinstance(preferences, Preferences):
        return preferences
    return Preferences(
        location=str(preferences.get("location", "")),
        budget=str(preferences.get("budget", "")),
        cuisine=str(preferences.get("cuisine", "")),
        min_rating=float(preferences["min_rating"]),
        notes=preferences.get("notes"),
    )


def _text(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _fold(value: Any) -> str:
    return _text(value).casefold()


def location_matches(location: Any, city: Any, query: str) -> bool:
    needle = query.strip().casefold()
    if not needle:
        return False
    loc = _fold(location)
    city_text = _fold(city)
    if loc and (needle in loc or loc in needle):
        return True
    if city_text and (needle in city_text or city_text in needle):
        return True
    return False


def cuisine_tokens(value: Any) -> set[str]:
    if value is None:
        return set()
    try:
        if pd.isna(value):
            return set()
    except (TypeError, ValueError):
        pass
    if isinstance(value, str):
        parts = value.split(",")
    elif isinstance(value, (list, tuple, set)):
        parts = list(value)
    else:
        try:
            parts = list(value)
        except TypeError:
            parts = [value]
    return {str(part).strip().casefold() for part in parts if str(part).strip()}


def cuisine_overlaps(catalog_cuisines: Any, query: str) -> bool:
    wanted = cuisine_tokens(query)
    if not wanted:
        return False
    have = cuisine_tokens(catalog_cuisines)
    return bool(wanted & have)


def _row_to_candidate(row: pd.Series) -> dict[str, Any]:
    cuisines = row["cuisines"] if "cuisines" in row.index else []
    if isinstance(cuisines, str):
        cuisines_list = [part.strip() for part in cuisines.split(",") if part.strip()]
    elif cuisines is None or (isinstance(cuisines, float) and pd.isna(cuisines)):
        cuisines_list = []
    else:
        try:
            cuisines_list = [str(part) for part in list(cuisines)]
        except TypeError:
            cuisines_list = [str(cuisines)]
    candidate: dict[str, Any] = {}
    for field in CANDIDATE_FIELDS:
        if field not in row.index:
            continue
        value = row[field]
        if field == "cuisines":
            candidate[field] = cuisines_list
        elif value is not None and not (isinstance(value, float) and pd.isna(value)):
            try:
                if pd.isna(value):
                    candidate[field] = None
                else:
                    candidate[field] = value.item() if hasattr(value, "item") else value
            except (TypeError, ValueError):
                candidate[field] = value
        else:
            candidate[field] = None if field in {"rating", "cost", "budget_band", "city", "extra"} else value
    return candidate


def filter_restaurants(
    catalog: pd.DataFrame,
    preferences: Preferences | Mapping[str, Any],
    *,
    shortlist_size: int | None = None,
) -> list[dict[str, Any]]:
    """Return a capped shortlist of catalog rows that match structured prefs.

    Filter order: location, cuisine, budget band, min rating. `notes` is not used.
    Over-constrained input yields `[]`; filters are never relaxed.
    """
    if catalog is None or catalog.empty:
        return []

    prefs = _as_preferences(preferences)
    cap = SHORTLIST_SIZE if shortlist_size is None else shortlist_size
    if cap < 1:
        return []

    budget = prefs.budget.strip().casefold()
    min_rating = float(prefs.min_rating)

    work = catalog.copy()
    loc_mask = work.apply(
        lambda row: location_matches(row.get("location"), row.get("city"), prefs.location),
        axis=1,
    )
    work = work.loc[loc_mask]
    if work.empty:
        return []

    cuisine_mask = work["cuisines"].map(lambda value: cuisine_overlaps(value, prefs.cuisine))
    work = work.loc[cuisine_mask]
    if work.empty:
        return []

    bands = work["budget_band"].astype("string").str.strip().str.casefold()
    work = work.loc[bands == budget]
    if work.empty:
        return []

    ratings = pd.to_numeric(work["rating"], errors="coerce")
    work = work.loc[ratings.notna() & (ratings >= min_rating)]
    if work.empty:
        return []

    work = work.assign(
        _rating=pd.to_numeric(work["rating"], errors="coerce"),
        _cost=pd.to_numeric(work["cost"], errors="coerce"),
    )
    work = work.sort_values(
        by=["_rating", "_cost"],
        ascending=[False, True],
        na_position="last",
        kind="mergesort",
    )
    work = work.drop_duplicates(subset=["id"], keep="first").head(cap)

    return [_row_to_candidate(row) for _, row in work.drop(columns=["_rating", "_cost"]).iterrows()]
