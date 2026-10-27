"""Request and response models for the recommendation API."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RecommendRequest(BaseModel):
    location: str = Field(min_length=1)
    budget: Literal["low", "medium", "high"]
    cuisine: str = Field(min_length=1)
    min_rating: float = Field(ge=0, le=5)
    notes: str | None = None
    top_k: int | None = Field(default=None, ge=1, le=50)

    @field_validator("location", "cuisine")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped

    @field_validator("notes")
    @classmethod
    def strip_optional_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class RecommendationItem(BaseModel):
    id: str
    rank: int
    name: str
    cuisines: list[str]
    rating: float | None = None
    cost: float | None = None
    location: str
    explanation: str


class RecommendResponse(BaseModel):
    status: Literal["ok", "no_matches"]
    summary: str | None = None
    source: Literal["llm", "fallback", "catalog"] | None = None
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    hint: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    catalog_loaded: bool
    detail: str | None = None


class BudgetCutoffs(BaseModel):
    low_max: float
    medium_max: float


class MetaResponse(BaseModel):
    cities: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    cuisines: list[str] = Field(default_factory=list)
    budget_cutoffs: BudgetCutoffs | None = None
