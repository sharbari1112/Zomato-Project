"""Phase 1: Hugging Face-like rows map to the canonical catalog schema."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.data.catalog import CatalogNotLoadedError, load_catalog
from app.data.ingest import ingest, persist_catalog
from app.data.transform import (
    CANONICAL_COLUMNS,
    IngestError,
    apply_budget_bands,
    normalize_source_frame,
    parse_cost,
    parse_rating,
)


def _hf_slice() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "name": ["Jalsa", "Spice Elephant", None, "  ", "Cafe A", "Unrated Joint"],
            "address": [
                "942, Banashankari, Bangalore",
                "80 Feet Road, Banashankari, Bangalore",
                "Somewhere",
                "Nowhere",
                "Indiranagar, Bangalore",
                "Koramangala, Bangalore",
            ],
            "location": ["Banashankari", "Banashankari", "X", "Y", "Indiranagar", "Koramangala"],
            "rate": ["4.1/5", "NEW", "3.0/5", "4.0/5", "4.0/5", "-"],
            "cuisines": [
                "North Indian, Mughlai, Chinese",
                "Chinese, North Indian, Thai",
                "Italian",
                "Italian",
                "Italian, Continental",
                "Cafe",
            ],
            "approx_cost(for two people)": ["800", "1,200", "300", "300", "Rs. 500", None],
            "rest_type": ["Casual Dining", "Casual Dining", "Cafe", "Cafe", "Cafe", "Cafe"],
            "votes": [775, 787, 1, 1, 10, 0],
        }
    )


def test_normalize_maps_hf_columns_to_canonical() -> None:
    catalog = normalize_source_frame(_hf_slice())
    assert list(catalog.columns) == CANONICAL_COLUMNS
    assert set(catalog["name"]) == {"Jalsa", "Spice Elephant", "Cafe A", "Unrated Joint"}
    jalsa = catalog.loc[catalog["name"] == "Jalsa"].iloc[0]
    assert jalsa["location"] == "Banashankari"
    assert jalsa["city"] == "Bangalore"
    assert jalsa["cuisines"] == ["North Indian", "Mughlai", "Chinese"]
    assert jalsa["rating"] == pytest.approx(4.1)
    assert jalsa["cost"] == pytest.approx(800.0)
    assert str(jalsa["id"]).startswith("r_")
    cafe = catalog.loc[catalog["name"] == "Cafe A"].iloc[0]
    assert cafe["cost"] == pytest.approx(500.0)


def test_missing_name_or_location_rows_are_dropped() -> None:
    catalog = normalize_source_frame(_hf_slice())
    assert "name" in catalog.columns
    assert catalog["name"].isna().sum() == 0
    assert catalog["location"].isna().sum() == 0
    assert len(catalog) == 4


def test_null_rating_and_cost_are_kept_not_invented() -> None:
    catalog = normalize_source_frame(_hf_slice())
    unrated = catalog.loc[catalog["name"] == "Unrated Joint"].iloc[0]
    assert pd.isna(unrated["rating"])
    assert pd.isna(unrated["cost"])
    elephant = catalog.loc[catalog["name"] == "Spice Elephant"].iloc[0]
    assert pd.isna(elephant["rating"])
    assert elephant["cost"] == pytest.approx(1200.0)


def test_budget_bands_assigned_for_rows_with_cost() -> None:
    catalog = normalize_source_frame(_hf_slice())
    catalog, cutoffs = apply_budget_bands(catalog, override="600,1000")
    assert cutoffs == (600.0, 1000.0)
    by_name = catalog.set_index("name")
    assert by_name.loc["Cafe A", "budget_band"] == "low"
    assert by_name.loc["Jalsa", "budget_band"] == "medium"
    assert by_name.loc["Spice Elephant", "budget_band"] == "high"
    assert pd.isna(by_name.loc["Unrated Joint", "budget_band"]) or by_name.loc["Unrated Joint", "budget_band"] is None


def test_budget_bands_from_tertiles() -> None:
    catalog = pd.DataFrame(
        {
            "id": ["a", "b", "c"],
            "name": ["A", "B", "C"],
            "location": ["L", "L", "L"],
            "city": ["Bangalore"] * 3,
            "cuisines": [["Italian"]] * 3,
            "rating": [4.0, 4.0, 4.0],
            "cost": [100.0, 200.0, 300.0],
            "budget_band": [None, None, None],
            "extra": ["{}"] * 3,
        }
    )
    catalog, cutoffs = apply_budget_bands(catalog)
    assert cutoffs is not None
    assert set(catalog["budget_band"]) <= {"low", "medium", "high"}
    assert catalog["budget_band"].notna().all()


def test_persist_refuses_empty_table(tmp_path: Path) -> None:
    dest = tmp_path / "catalog.parquet"
    with pytest.raises(IngestError, match="empty catalog"):
        persist_catalog(pd.DataFrame(columns=CANONICAL_COLUMNS), dest)
    assert not dest.exists()


def test_persist_refuses_too_few_rows(tmp_path: Path) -> None:
    dest = tmp_path / "catalog.parquet"
    catalog = normalize_source_frame(_hf_slice())
    with pytest.raises(IngestError, match="at least"):
        persist_catalog(catalog, dest, min_rows=10_000)
    assert not dest.exists()


def test_ingest_with_injected_loader_writes_parquet(tmp_path: Path) -> None:
    dest = tmp_path / "catalog.parquet"

    def loader(_dataset_id: str) -> pd.DataFrame:
        return _hf_slice()

    written = ingest(
        dataset_id="test/fixture",
        dest=dest,
        budget_cutoffs_override="600,1000",
        min_rows=1,
        source_loader=loader,
        write_notes=False,
    )
    assert written == dest
    loaded = load_catalog(dest)
    assert len(loaded) == 4
    assert list(loaded.columns) == CANONICAL_COLUMNS


def test_load_catalog_missing_file(tmp_path: Path) -> None:
    with pytest.raises(CatalogNotLoadedError):
        load_catalog(tmp_path / "missing.parquet")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("4.1/5", 4.1),
        ("NEW", None),
        ("-", None),
        ("", None),
        (4.3, 4.3),
    ],
)
def test_parse_rating(raw: object, expected: float | None) -> None:
    got = parse_rating(raw)
    if expected is None:
        assert got is None
    else:
        assert got == pytest.approx(expected)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1,200", 1200.0),
        ("Rs. 800", 800.0),
        (None, None),
    ],
)
def test_parse_cost(raw: object, expected: float | None) -> None:
    got = parse_cost(raw)
    if expected is None:
        assert got is None
    else:
        assert got == pytest.approx(expected)


def test_huggingface_unreachable_does_not_write(tmp_path: Path) -> None:
    dest = tmp_path / "catalog.parquet"

    def loader(_dataset_id: str) -> pd.DataFrame:
        raise IngestError("Could not load Hugging Face dataset")

    with pytest.raises(IngestError, match="Could not load"):
        ingest(dest=dest, min_rows=1, source_loader=loader, write_notes=False)
    assert not dest.exists()
