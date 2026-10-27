"""API routes: health, meta, and recommendations (filter + LLM/fallback)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import (
    HealthResponse,
    MetaResponse,
    RecommendRequest,
    RecommendResponse,
)
from app.data.meta import build_catalog_meta
from app.recommend.service import recommend

router = APIRouter()


def _require_catalog(request: Request):
    catalog = getattr(request.app.state, "catalog", None)
    if catalog is None:
        detail = getattr(request.app.state, "catalog_error", None) or (
            "Catalog not loaded. Run `python -m app.data.ingest` and restart the API."
        )
        raise HTTPException(status_code=503, detail=detail)
    return catalog


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    """Process up; 503 when the catalog is missing."""
    catalog = getattr(request.app.state, "catalog", None)
    if catalog is None:
        detail = getattr(request.app.state, "catalog_error", None) or "Catalog not loaded"
        raise HTTPException(status_code=503, detail=detail)
    return HealthResponse(status="ok", catalog_loaded=True, detail=None)


@router.get("/meta", response_model=MetaResponse)
def meta(request: Request) -> MetaResponse:
    """Distinct cities/locations, sample cuisines, and budget cutoffs for UI dropdowns."""
    catalog = _require_catalog(request)
    return MetaResponse(**build_catalog_meta(catalog))


@router.post("/recommend", response_model=RecommendResponse)
def post_recommend(body: RecommendRequest, request: Request) -> RecommendResponse:
    """Validate prefs, filter catalog, LLM-rank or fallback (or no_matches)."""
    catalog = _require_catalog(request)
    return recommend(catalog, body)
