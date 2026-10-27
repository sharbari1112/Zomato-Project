"""Phase 2: structured filters on a tiny in-memory catalog."""

from __future__ import annotations

import pandas as pd

from app.recommend.filters import Preferences, filter_restaurants


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
                "id": "r2",
                "name": "Spice House",
                "location": "Banashankari",
                "city": "Bangalore",
                "cuisines": ["Chinese"],
                "rating": 4.4,
                "cost": 450.0,
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
            {
                "id": "r5",
                "name": "Delhi Trattoria",
                "location": "Connaught Place",
                "city": "Delhi",
                "cuisines": ["Italian"],
                "rating": 4.6,
                "cost": 500.0,
                "budget_band": "medium",
                "extra": "{}",
            },
            {
                "id": "r6",
                "name": "Unrated Italian",
                "location": "Banashankari",
                "city": "Bangalore",
                "cuisines": ["Italian"],
                "rating": None,
                "budget_band": "medium",
                "cost": 400.0,
                "extra": "{}",
            },
            {
                "id": "r7",
                "name": "Cheap Italian",
                "location": "Banashankari",
                "city": "Bangalore",
                "cuisines": ["Italian"],
                "rating": 4.5,
                "cost": 200.0,
                "budget_band": "low",
                "extra": "{}",
            },
            {
                "id": "r8",
                "name": "Low Rated Italian",
                "location": "Banashankari",
                "city": "Bangalore",
                "cuisines": ["Italian"],
                "rating": 3.1,
                "cost": 400.0,
                "budget_band": "medium",
                "extra": "{}",
            },
        ]
    )


def _prefs(**overrides: object) -> Preferences:
    base = dict(
        location="Banashankari",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
        notes="family-friendly",
    )
    base.update(overrides)
    return Preferences(**base)  # type: ignore[arg-type]


def _ids(rows: list[dict]) -> list[str]:
    return [row["id"] for row in rows]


def test_location_excludes_other_neighborhoods() -> None:
    ids = set(_ids(filter_restaurants(_catalog(), _prefs())))
    assert "r1" in ids
    assert "r3" not in ids
    assert "r5" not in ids


def test_location_is_case_insensitive_and_contains() -> None:
    ids = _ids(filter_restaurants(_catalog(), _prefs(location="banashankari")))
    assert ids == ["r1"]
    koramangala = _ids(
        filter_restaurants(
            _catalog(),
            _prefs(location="koramangala", budget="high", cuisine="Italian", min_rating=4.0),
        )
    )
    assert koramangala == ["r4"]


def test_location_matches_city() -> None:
    ids = set(
        _ids(
            filter_restaurants(
                _catalog(),
                _prefs(location="Bangalore", cuisine="Italian", budget="medium", min_rating=4.0),
            )
        )
    )
    assert ids == {"r1", "r3"}
    assert "r5" not in ids


def test_cuisine_excludes_non_overlapping() -> None:
    ids = set(_ids(filter_restaurants(_catalog(), _prefs())))
    assert "r1" in ids
    assert "r2" not in ids


def test_cuisine_overlap_and_case() -> None:
    ids = _ids(
        filter_restaurants(
            _catalog(),
            _prefs(location="Indiranagar", cuisine="italian", budget="medium", min_rating=4.0),
        )
    )
    assert ids == ["r3"]


def test_budget_excludes_other_bands() -> None:
    ids = set(_ids(filter_restaurants(_catalog(), _prefs())))
    assert "r1" in ids
    assert "r4" not in ids
    assert "r7" not in ids


def test_rating_excludes_low_and_missing() -> None:
    ids = set(_ids(filter_restaurants(_catalog(), _prefs())))
    assert "r1" in ids
    assert "r6" not in ids
    assert "r8" not in ids


def test_combined_filters_yield_expected_ids() -> None:
    assert _ids(filter_restaurants(_catalog(), _prefs())) == ["r1"]


def test_overconstrained_returns_empty() -> None:
    assert (
        filter_restaurants(
            _catalog(),
            _prefs(location="Banashankari", cuisine="Italian", budget="high", min_rating=4.0),
        )
        == []
    )
    assert filter_restaurants(_catalog(), _prefs(location="Mars")) == []


def test_notes_do_not_filter() -> None:
    with_notes = _ids(filter_restaurants(_catalog(), _prefs(notes="only Chinese please")))
    without_notes = _ids(filter_restaurants(_catalog(), _prefs(notes=None)))
    assert with_notes == without_notes == ["r1"]


def test_shortlist_cap_keeps_highest_rated() -> None:
    rows = []
    for i in range(8):
        rows.append(
            {
                "id": f"c{i}",
                "name": f"Place {i}",
                "location": "BTM",
                "city": "Bangalore",
                "cuisines": ["Italian"],
                "rating": 4.0 + i * 0.1,
                "cost": 100.0 + i,
                "budget_band": "medium",
                "extra": "{}",
            }
        )
    catalog = pd.DataFrame(rows)
    prefs = Preferences(location="BTM", budget="medium", cuisine="Italian", min_rating=4.0)
    shortlist = filter_restaurants(catalog, prefs, shortlist_size=3)
    assert _ids(shortlist) == ["c7", "c6", "c5"]
    assert len(shortlist) <= 3


def test_equal_rating_breaks_ties_by_lower_cost() -> None:
    catalog = pd.DataFrame(
        [
            {
                "id": "expensive",
                "name": "A",
                "location": "HSR",
                "city": "Bangalore",
                "cuisines": ["Italian"],
                "rating": 4.2,
                "cost": 800.0,
                "budget_band": "medium",
                "extra": "{}",
            },
            {
                "id": "cheap",
                "name": "B",
                "location": "HSR",
                "city": "Bangalore",
                "cuisines": ["Italian"],
                "rating": 4.2,
                "cost": 400.0,
                "budget_band": "medium",
                "extra": "{}",
            },
        ]
    )
    prefs = Preferences(location="HSR", budget="medium", cuisine="Italian", min_rating=4.0)
    assert _ids(filter_restaurants(catalog, prefs)) == ["cheap", "expensive"]


def test_accepts_plain_dict_preferences() -> None:
    ids = _ids(
        filter_restaurants(
            _catalog(),
            {
                "location": "Banashankari",
                "budget": "medium",
                "cuisine": "Italian",
                "min_rating": 4.0,
            },
        )
    )
    assert ids == ["r1"]


def test_duplicate_ids_keep_one_row() -> None:
    catalog = pd.DataFrame(
        [
            {
                "id": "dup",
                "name": "Onesta",
                "location": "Banashankari",
                "city": "Bangalore",
                "cuisines": ["Italian"],
                "rating": 4.6,
                "cost": 600.0,
                "budget_band": "medium",
                "extra": "{}",
            },
            {
                "id": "dup",
                "name": "Onesta",
                "location": "Banashankari",
                "city": "Bangalore",
                "cuisines": ["Italian"],
                "rating": 4.6,
                "cost": 600.0,
                "budget_band": "medium",
                "extra": "{}",
            },
            {
                "id": "other",
                "name": "Other",
                "location": "Banashankari",
                "city": "Bangalore",
                "cuisines": ["Italian"],
                "rating": 4.1,
                "cost": 500.0,
                "budget_band": "medium",
                "extra": "{}",
            },
        ]
    )
    ids = _ids(filter_restaurants(catalog, _prefs()))
    assert ids == ["dup", "other"]


def test_candidate_dicts_include_catalog_fields() -> None:
    row = filter_restaurants(_catalog(), _prefs())[0]
    assert row["name"] == "Jalsa"
    assert row["location"] == "Banashankari"
    assert "Italian" in row["cuisines"]
    assert row["rating"] == 4.5
    assert row["cost"] == 500.0
    assert row["budget_band"] == "medium"
