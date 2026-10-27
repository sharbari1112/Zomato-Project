"""Deterministic rating/cost rank when the LLM path fails."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from app.api.schemas import RecommendationItem


def _preferences_mapping(preferences: Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(preferences, Mapping):
        return {
            "location": preferences.get("location"),
            "budget": preferences.get("budget"),
            "cuisine": preferences.get("cuisine"),
            "min_rating": preferences.get("min_rating"),
            "notes": preferences.get("notes"),
        }
    return {
        "location": getattr(preferences, "location", None),
        "budget": getattr(preferences, "budget", None),
        "cuisine": getattr(preferences, "cuisine", None),
        "min_rating": getattr(preferences, "min_rating", None),
        "notes": getattr(preferences, "notes", None),
    }


def _sort_key(row: Mapping[str, Any]) -> tuple[float, float]:
    rating = row.get("rating")
    cost = row.get("cost")
    rating_key = float(rating) if rating is not None else float("-inf")
    cost_key = float(cost) if cost is not None else float("inf")
    return (-rating_key, cost_key)


def canned_explanation(candidate: Mapping[str, Any], preferences: Mapping[str, Any]) -> str:
    """Filter-match sentence; display facts still come from the candidate row."""
    location = preferences.get("location") or "the requested area"
    cuisine = preferences.get("cuisine") or "the requested cuisine"
    budget = preferences.get("budget") or "the requested"
    min_rating = preferences.get("min_rating")
    rating = candidate.get("rating")
    rating_bit = (
        f"rating {rating} (≥ {min_rating})"
        if rating is not None and min_rating is not None
        else ("rating available" if rating is not None else "rating filter passed")
    )
    return (
        f"Matches {cuisine} near {location} on a {budget} budget "
        f"({rating_bit}). Ranked by rating then cost when the model was unavailable."
    )


def fallback_rank(
    shortlist: Sequence[Mapping[str, Any]],
    preferences: Mapping[str, Any] | Any,
    top_k: int,
) -> tuple[str, list[RecommendationItem]]:
    """Sort shortlist by rating desc, cost asc; return up to `top_k` catalog-backed cards."""
    if top_k < 1:
        return "No recommendations available.", []

    prefs = _preferences_mapping(preferences)
    ordered = sorted(shortlist, key=_sort_key)
    items: list[RecommendationItem] = []
    for row in ordered[:top_k]:
        cuisines = row.get("cuisines") or []
        if not isinstance(cuisines, list):
            cuisines = [str(cuisines)]
        rating = row.get("rating")
        cost = row.get("cost")
        items.append(
            RecommendationItem(
                id=str(row["id"]),
                rank=len(items) + 1,
                name=str(row["name"]),
                cuisines=[str(c) for c in cuisines],
                rating=float(rating) if rating is not None else None,
                cost=float(cost) if cost is not None else None,
                location=str(row.get("location") or ""),
                explanation=canned_explanation(row, prefs),
            )
        )

    summary = (
        "Showing top matches by rating and cost. Explanations are rule-based "
        "because the language model was unavailable or returned unusable results."
    )
    return summary, items
