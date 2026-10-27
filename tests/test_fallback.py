"""Phase 5: deterministic fallback, repair retry, and service isolation."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from app.api.schemas import RecommendRequest
from app.recommend.engine import EngineError, rank_shortlist
from app.recommend.fallback import fallback_rank
from app.recommend.service import clear_recommend_cache, recommend


def _shortlist() -> list[dict]:
    return [
        {
            "id": "r1",
            "name": "Jalsa",
            "location": "Banashankari",
            "cuisines": ["North Indian", "Italian"],
            "rating": 4.5,
            "cost": 500.0,
            "budget_band": "medium",
        },
        {
            "id": "r3",
            "name": "Pasta Place",
            "location": "Indiranagar",
            "cuisines": ["Italian", "Continental"],
            "rating": 4.2,
            "cost": 550.0,
            "budget_band": "medium",
        },
        {
            "id": "r2",
            "name": "Cheap Pasta",
            "location": "Banashankari",
            "cuisines": ["Italian"],
            "rating": 4.5,
            "cost": 400.0,
            "budget_band": "medium",
        },
    ]


def _prefs() -> dict:
    return {
        "location": "Banashankari",
        "budget": "medium",
        "cuisine": "Italian",
        "min_rating": 4.0,
        "notes": "family-friendly",
    }


def _catalog() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": "r1",
                "name": "Jalsa",
                "location": "Banashankari",
                "city": "Bangalore",
                "cuisines": ["North Indian", "Italian"],
                "rating": 4.5,
                "cost": 500.0,
                "budget_band": "medium",
                "extra": "{}",
            },
            {
                "id": "r3",
                "name": "Pasta Place",
                "location": "Indiranagar",
                "city": "Bangalore",
                "cuisines": ["Italian", "Continental"],
                "rating": 4.2,
                "cost": 550.0,
                "budget_band": "medium",
                "extra": "{}",
            },
        ]
    )


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_recommend_cache()
    yield
    clear_recommend_cache()


def test_fallback_sorts_by_rating_then_cost() -> None:
    summary, items = fallback_rank(_shortlist(), _prefs(), top_k=3)
    assert "rule-based" in summary.casefold() or "rating" in summary.casefold()
    assert [item.id for item in items] == ["r2", "r1", "r3"]
    assert items[0].name == "Cheap Pasta"
    assert items[0].rating == 4.5
    assert items[0].cost == 400.0
    assert "Italian" in items[0].explanation
    assert "Banashankari" in items[0].explanation
    assert items[0].rank == 1


def test_fallback_respects_top_k() -> None:
    _, items = fallback_rank(_shortlist(), _prefs(), top_k=1)
    assert len(items) == 1
    assert items[0].id == "r2"


def test_mock_llm_failure_returns_fallback_cards() -> None:
    def boom(_messages: list[dict[str, str]]) -> str:
        raise EngineError("Groq request failed: mocked")

    response = recommend(
        _catalog(),
        RecommendRequest(
            location="Banashankari",
            budget="medium",
            cuisine="Italian",
            min_rating=4.0,
            top_k=5,
        ),
        llm_complete=boom,
    )
    assert response.status == "ok"
    assert response.source == "fallback"
    assert len(response.recommendations) == 1
    item = response.recommendations[0]
    assert item.id == "r1"
    assert item.name == "Jalsa"
    assert item.rating == 4.5
    assert item.cost == 500.0
    assert item.explanation


def test_all_invalid_ids_fall_back() -> None:
    def complete(_messages: list[dict[str, str]]) -> str:
        return json.dumps(
            {
                "summary": "Nope",
                "ranked_ids": [{"id": "r999", "explanation": "invented"}],
            }
        )

    response = recommend(
        _catalog(),
        RecommendRequest(
            location="Banashankari",
            budget="medium",
            cuisine="Italian",
            min_rating=4.0,
            top_k=3,
        ),
        llm_complete=complete,
    )
    assert response.status == "ok"
    assert response.source == "fallback"
    assert [item.id for item in response.recommendations] == ["r1"]


def test_repair_then_success() -> None:
    calls = {"n": 0}

    def complete(_messages: list[dict[str, str]]) -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            return "not json at all"
        return json.dumps(
            {
                "summary": "Recovered after repair.",
                "ranked_ids": [
                    {"id": "r3", "explanation": "Solid Italian pick."},
                ],
            }
        )

    summary, items = rank_shortlist(_shortlist(), _prefs(), top_k=2, complete=complete)
    assert calls["n"] == 2
    assert summary == "Recovered after repair."
    assert [item.id for item in items] == ["r3"]
    assert items[0].name == "Pasta Place"


def test_repair_then_fallback_when_still_bad() -> None:
    calls = {"n": 0}

    def complete(_messages: list[dict[str, str]]) -> str:
        calls["n"] += 1
        return "{{{still broken"

    response = recommend(
        _catalog(),
        RecommendRequest(
            location="Banashankari",
            budget="medium",
            cuisine="Italian",
            min_rating=4.0,
            top_k=2,
        ),
        llm_complete=complete,
    )
    assert calls["n"] == 2
    assert response.status == "ok"
    assert response.source == "fallback"
    assert response.recommendations[0].id == "r1"
