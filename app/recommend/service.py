"""Filter then LLM-rank with deterministic fallback. Display fields from catalog."""

from __future__ import annotations

import hashlib
import json
import threading
import time

import pandas as pd

from app.api.schemas import RecommendRequest, RecommendResponse
from app.config import CACHE_TTL_SECONDS, DEFAULT_TOP_K
from app.recommend.engine import CompleteFn, EngineError, rank_shortlist
from app.recommend.fallback import fallback_rank
from app.recommend.filters import Preferences, filter_restaurants

NO_MATCHES_HINT = (
    "No restaurants matched location, cuisine, budget, and rating together. "
    "Relax one constraint."
)

_cache_lock = threading.Lock()
_response_cache: dict[str, tuple[float, RecommendResponse]] = {}


def _cache_key(request: RecommendRequest, shortlist_size: int | None) -> str:
    payload = {
        "location": request.location,
        "budget": request.budget,
        "cuisine": request.cuisine,
        "min_rating": request.min_rating,
        "notes": request.notes,
        "top_k": request.top_k,
        "shortlist_size": shortlist_size,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_get(key: str) -> RecommendResponse | None:
    if CACHE_TTL_SECONDS <= 0:
        return None
    now = time.monotonic()
    with _cache_lock:
        entry = _response_cache.get(key)
        if entry is None:
            return None
        expires_at, response = entry
        if now >= expires_at:
            _response_cache.pop(key, None)
            return None
        return response.model_copy(deep=True)


def _cache_set(key: str, response: RecommendResponse) -> None:
    if CACHE_TTL_SECONDS <= 0:
        return
    with _cache_lock:
        _response_cache[key] = (
            time.monotonic() + CACHE_TTL_SECONDS,
            response.model_copy(deep=True),
        )


def clear_recommend_cache() -> None:
    """Test helper: drop the in-memory preference cache."""
    with _cache_lock:
        _response_cache.clear()


def recommend(
    catalog: pd.DataFrame,
    request: RecommendRequest,
    *,
    shortlist_size: int | None = None,
    llm_complete: CompleteFn | None = None,
) -> RecommendResponse:
    """Filter the catalog; LLM-rank on hits, else fallback; never invent rows."""
    cache_key = _cache_key(request, shortlist_size)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    top_k = DEFAULT_TOP_K if request.top_k is None else request.top_k
    prefs = Preferences(
        location=request.location,
        budget=request.budget,
        cuisine=request.cuisine,
        min_rating=request.min_rating,
        notes=request.notes,
    )
    shortlist = filter_restaurants(catalog, prefs, shortlist_size=shortlist_size)
    if not shortlist:
        response = RecommendResponse(
            status="no_matches",
            summary=None,
            source=None,
            recommendations=[],
            hint=NO_MATCHES_HINT,
        )
        _cache_set(cache_key, response)
        return response

    try:
        summary, items = rank_shortlist(
            shortlist,
            request,
            top_k,
            complete=llm_complete,
        )
        response = RecommendResponse(
            status="ok",
            summary=summary,
            source="llm",
            recommendations=items,
            hint=None,
        )
    except EngineError:
        summary, items = fallback_rank(shortlist, request, top_k)
        response = RecommendResponse(
            status="ok",
            summary=summary,
            source="fallback",
            recommendations=items,
            hint=None,
        )

    _cache_set(cache_key, response)
    return response
