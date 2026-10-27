"""Phase 4: prompt builder + LLM ID validation (mocked Groq)."""

from __future__ import annotations

import json

import pytest

from app.recommend.engine import EngineError, join_ranked_to_candidates, parse_ranked_payload, rank_shortlist
from app.recommend.prompts import SYSTEM_PROMPT, build_messages, build_user_prompt


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
            "extra": "{}",
        },
        {
            "id": "r3",
            "name": "Pasta Place",
            "location": "Indiranagar",
            "cuisines": ["Italian", "Continental"],
            "rating": 4.2,
            "cost": 550.0,
            "budget_band": "medium",
            "extra": "{}",
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


def test_prompt_includes_all_shortlist_ids_and_notes() -> None:
    shortlist = _shortlist()
    user = build_user_prompt(_prefs(), shortlist, top_k=2)
    assert "r1" in user
    assert "r3" in user
    assert "family-friendly" in user
    assert "Italian" in user
    # Token-lean payload: no redundant budget_band / empty extra; compact JSON.
    assert "budget_band" not in user
    assert "extra" not in user
    assert '": "' not in user  # separators=(",", ":") — no space after colon
    messages = build_messages(_prefs(), shortlist, top_k=2)
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == SYSTEM_PROMPT
    assert "CANDIDATES" in messages[1]["content"]
    assert "ignore" in SYSTEM_PROMPT.casefold() or "Ignore" in SYSTEM_PROMPT


def test_empty_notes_omitted_from_prompt() -> None:
    prefs = {**_prefs(), "notes": "   "}
    user = build_user_prompt(prefs, _shortlist(), top_k=2)
    assert "notes" not in user


def test_unknown_id_from_llm_is_stripped() -> None:
    ranked = [
        {"id": "invented", "explanation": "fake"},
        {"id": "r3", "explanation": "Solid Italian pick."},
        {"id": "r1", "explanation": "Closest to Banashankari."},
    ]
    items = join_ranked_to_candidates(ranked, _shortlist(), top_k=5)
    assert [item.id for item in items] == ["r3", "r1"]
    assert all(item.id != "invented" for item in items)


def test_valid_ids_preserve_order_and_catalog_fields() -> None:
    def complete(_messages: list[dict[str, str]]) -> str:
        return json.dumps(
            {
                "summary": "Italian picks that fit a medium budget.",
                "ranked_ids": [
                    {"id": "r3", "explanation": "Good Indiranagar Italian option."},
                    {"id": "r1", "explanation": "Closest Banashankari match."},
                    {"id": "r999", "explanation": "Should be dropped."},
                ],
            }
        )

    summary, items = rank_shortlist(_shortlist(), _prefs(), top_k=5, complete=complete)
    assert summary == "Italian picks that fit a medium budget."
    assert [item.id for item in items] == ["r3", "r1"]
    assert items[0].name == "Pasta Place"
    assert items[0].rating == 4.2
    assert items[0].cost == 550.0
    assert items[0].explanation == "Good Indiranagar Italian option."
    assert items[1].name == "Jalsa"
    assert items[1].rating == 4.5
    assert items[1].cost == 500.0
    assert items[0].rank == 1
    assert items[1].rank == 2


def test_top_k_caps_joined_results() -> None:
    ranked = [
        {"id": "r3", "explanation": "A"},
        {"id": "r1", "explanation": "B"},
    ]
    items = join_ranked_to_candidates(ranked, _shortlist(), top_k=1)
    assert len(items) == 1
    assert items[0].id == "r3"


def test_all_unknown_ids_raise() -> None:
    def complete(_messages: list[dict[str, str]]) -> str:
        return json.dumps(
            {
                "summary": "Nope",
                "ranked_ids": [{"id": "r999", "explanation": "invented"}],
            }
        )

    with pytest.raises(EngineError, match="no IDs that exist"):
        rank_shortlist(_shortlist(), _prefs(), top_k=3, complete=complete)


def test_parse_ranked_payload_rejects_non_object() -> None:
    with pytest.raises(EngineError):
        parse_ranked_payload("[1, 2]")
