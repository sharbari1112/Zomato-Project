"""API contract for /recommend, /health, and /meta (Phases 3–5)."""

from __future__ import annotations

import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.recommend.engine import EngineError
from app.recommend.service import NO_MATCHES_HINT, clear_recommend_cache


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
            {
                "id": "r4",
                "name": "Fine Italian",
                "location": "Koramangala 5th Block",
                "city": "Bangalore",
                "cuisines": ["Italian"],
                "rating": 4.8,
                "cost": 1500.0,
                "budget_band": "high",
                "extra": "{}",
            },
        ]
    )


def _mock_complete_from_shortlist_order(messages: list[dict[str, str]]) -> str:
    """Deterministic stand-in for Groq: rank shortlist IDs in catalog order."""
    user = messages[1]["content"]
    if "CANDIDATES:" in user:
        payload = json.loads(user.split("CANDIDATES:", 1)[1])
        ranked = [
            {
                "id": row["id"],
                "explanation": f"Mock explanation for {row.get('name', row['id'])}.",
            }
            for row in payload
        ]
    else:
        ids = json.loads(user.split("CANDIDATE_IDS:", 1)[1])
        ranked = [
            {"id": item_id, "explanation": f"Mock explanation for {item_id}."}
            for item_id in ids
        ]
    return json.dumps(
        {
            "summary": "Mock LLM summary for the filtered shortlist.",
            "ranked_ids": ranked,
        }
    )


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_recommend_cache()
    yield
    clear_recommend_cache()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(
        "app.recommend.engine.complete_chat_groq",
        _mock_complete_from_shortlist_order,
    )
    with TestClient(app) as test_client:
        test_client.app.state.catalog = _catalog()
        test_client.app.state.catalog_error = None
        yield test_client


def test_health_ok_when_catalog_loaded(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["catalog_loaded"] is True


def test_plate_match_ui_served(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "PlateMatch" in response.text
    assert "/assets/config.js" in response.text
    assets = client.get("/assets/app.js")
    assert assets.status_code == 200
    assert "recommend" in assets.text
    assert "API_BASE" in assets.text
    config = client.get("/assets/config.js")
    assert config.status_code == 200
    assert "__API_BASE__" in config.text


def test_health_503_when_catalog_missing() -> None:
    with TestClient(app) as test_client:
        test_client.app.state.catalog = None
        test_client.app.state.catalog_error = "missing"
        response = test_client.get("/health")
        assert response.status_code == 503


def test_meta_returns_catalog_samples(client: TestClient) -> None:
    response = client.get("/meta")
    assert response.status_code == 200
    body = response.json()
    assert "Bangalore" in body["cities"]
    assert "Banashankari" in body["locations"]
    assert "Italian" in body["cuisines"]
    assert body["budget_cutoffs"] is not None
    assert body["budget_cutoffs"]["low_max"] <= body["budget_cutoffs"]["medium_max"]


def test_meta_503_when_catalog_missing() -> None:
    with TestClient(app) as test_client:
        test_client.app.state.catalog = None
        test_client.app.state.catalog_error = "missing"
        response = test_client.get("/meta")
        assert response.status_code == 503


def test_recommend_ok_includes_card_fields(client: TestClient) -> None:
    response = client.post(
        "/recommend",
        json={
            "location": "Banashankari",
            "budget": "medium",
            "cuisine": "Italian",
            "min_rating": 4.0,
            "notes": "family-friendly",
            "top_k": 5,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["source"] == "llm"
    assert body["summary"]
    assert len(body["recommendations"]) == 1
    item = body["recommendations"][0]
    assert item["id"] == "r1"
    assert item["name"] == "Jalsa"
    assert "Italian" in item["cuisines"]
    assert item["rating"] == 4.5
    assert item["cost"] == 500.0
    assert item["location"] == "Banashankari"
    assert item["explanation"]
    assert item["rank"] == 1


def test_recommend_no_matches(client: TestClient) -> None:
    response = client.post(
        "/recommend",
        json={
            "location": "Banashankari",
            "budget": "medium",
            "cuisine": "Italian",
            "min_rating": 4.9,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_matches"
    assert body["recommendations"] == []
    assert body["hint"] == NO_MATCHES_HINT
    assert body["summary"] is None


def test_recommend_422_on_invalid_budget(client: TestClient) -> None:
    response = client.post(
        "/recommend",
        json={
            "location": "Banashankari",
            "budget": "luxury",
            "cuisine": "Italian",
            "min_rating": 4.0,
        },
    )
    assert response.status_code == 422


def test_recommend_422_on_empty_location(client: TestClient) -> None:
    response = client.post(
        "/recommend",
        json={
            "location": "   ",
            "budget": "medium",
            "cuisine": "Italian",
            "min_rating": 4.0,
        },
    )
    assert response.status_code == 422


def test_recommend_503_when_catalog_missing() -> None:
    with TestClient(app) as test_client:
        test_client.app.state.catalog = None
        test_client.app.state.catalog_error = "missing"
        response = test_client.post(
            "/recommend",
            json={
                "location": "Banashankari",
                "budget": "medium",
                "cuisine": "Italian",
                "min_rating": 4.0,
            },
        )
        assert response.status_code == 503


def test_recommend_respects_top_k(client: TestClient) -> None:
    response = client.post(
        "/recommend",
        json={
            "location": "Bangalore",
            "budget": "medium",
            "cuisine": "Italian",
            "min_rating": 4.0,
            "top_k": 1,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["source"] == "llm"
    assert len(body["recommendations"]) == 1
    assert body["recommendations"][0]["id"] == "r1"


def test_recommend_fallback_when_llm_fails(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(_messages: list[dict[str, str]]) -> str:
        raise EngineError("Groq request failed: mocked")

    monkeypatch.setattr("app.recommend.engine.complete_chat_groq", boom)
    response = client.post(
        "/recommend",
        json={
            "location": "Banashankari",
            "budget": "medium",
            "cuisine": "Italian",
            "min_rating": 4.0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["source"] == "fallback"
    assert len(body["recommendations"]) == 1
    item = body["recommendations"][0]
    assert item["id"] == "r1"
    assert item["name"] == "Jalsa"
    assert item["rating"] == 4.5
    assert item["cost"] == 500.0
    assert item["explanation"]
