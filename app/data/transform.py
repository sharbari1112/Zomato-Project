"""Map Hugging Face-like restaurant rows onto the canonical catalog schema."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

CANONICAL_COLUMNS = [
    "id",
    "name",
    "location",
    "city",
    "cuisines",
    "rating",
    "cost",
    "budget_band",
    "extra",
]

_NAME_ALIASES = ("name",)
_LOCATION_ALIASES = ("location",)
_CITY_ALIASES = ("city",)
_CUISINE_ALIASES = ("cuisines", "cuisine")
_RATING_ALIASES = ("rate", "rating")
_COST_ALIASES = ("approx_cost(for two people)", "approx_cost", "cost")
_ADDRESS_ALIASES = ("address",)

_UNRATED = frozenset({"", "nan", "none", "null", "new", "-", "--", "unrated"})

_KNOWN_CITIES = (
    ("new delhi", "Delhi"),
    ("delhi", "Delhi"),
    ("bengaluru", "Bangalore"),
    ("bangalore", "Bangalore"),
    ("mumbai", "Mumbai"),
    ("hyderabad", "Hyderabad"),
    ("chennai", "Chennai"),
    ("kolkata", "Kolkata"),
    ("pune", "Pune"),
)


class IngestError(RuntimeError):
    """Raised when catalog ingest cannot produce a usable file."""


def _first_present(frame: pd.DataFrame, aliases: tuple[str, ...]) -> str | None:
    lower = {str(col).lower(): col for col in frame.columns}
    for alias in aliases:
        if alias.lower() in lower:
            return lower[alias.lower()]
    return None


def _clean_text(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    if text.lower() in _UNRATED:
        return None
    return text or None


def parse_rating(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        return number if math.isfinite(number) else None
    text = str(value).strip()
    if text.lower() in _UNRATED:
        return None
    text = text.split("/")[0].strip()
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def parse_cost(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        return number if math.isfinite(number) else None
    text = re.sub(r"(?i)(?:rs\.?|₹)", "", str(value))
    text = text.replace(",", "")
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        number = float(match.group(0))
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def parse_cuisines(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    if isinstance(value, list):
        return [part.strip() for part in value if str(part).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def infer_city(address: str | None, location: str | None, explicit: str | None) -> str | None:
    if explicit:
        lowered = explicit.lower()
        for needle, canonical in _KNOWN_CITIES:
            if needle in lowered:
                return canonical
        return explicit
    blob = f"{address or ''} {location or ''}".lower()
    for needle, canonical in _KNOWN_CITIES:
        if needle in blob:
            return canonical
    return None


def make_id(name: str, address: str | None, location: str) -> str:
    key = f"{name}|{address or ''}|{location}"
    return "r_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def parse_budget_cutoffs(override: str | None) -> tuple[float, float] | None:
    if override is None or not str(override).strip():
        return None
    parts = [part.strip() for part in str(override).split(",")]
    if len(parts) != 2:
        raise IngestError("BUDGET_CUTOFFS must be two numbers, e.g. 500,1000")
    try:
        low_max, medium_max = float(parts[0]), float(parts[1])
    except ValueError as exc:
        raise IngestError("BUDGET_CUTOFFS must be two numbers, e.g. 500,1000") from exc
    if not (low_max < medium_max):
        raise IngestError("BUDGET_CUTOFFS requires low_max < medium_max")
    return low_max, medium_max


def compute_budget_cutoffs(
    costs: pd.Series,
    override: str | None = None,
) -> tuple[float, float] | None:
    parsed = parse_budget_cutoffs(override)
    if parsed is not None:
        logger.info("Budget cutoffs from BUDGET_CUTOFFS: low<=%s, medium<=%s", parsed[0], parsed[1])
        return parsed
    valid = pd.to_numeric(costs, errors="coerce").dropna()
    if valid.empty:
        logger.warning("No numeric costs; budget_band will be null for all rows")
        return None
    low_max = float(valid.quantile(1 / 3))
    medium_max = float(valid.quantile(2 / 3))
    logger.info("Budget cutoffs from cost tertiles: low<=%s, medium<=%s", low_max, medium_max)
    return low_max, medium_max


def assign_budget_band(cost: float | None, cutoffs: tuple[float, float] | None) -> str | None:
    if cost is None or (isinstance(cost, float) and math.isnan(cost)) or cutoffs is None:
        return None
    low_max, medium_max = cutoffs
    if cost <= low_max:
        return "low"
    if cost <= medium_max:
        return "medium"
    return "high"


def _row_extra(row: pd.Series) -> str:
    extra: dict[str, Any] = {}
    for key in ("rest_type", "listed_in(type)", "listed_in(city)", "votes", "online_order", "book_table"):
        if key in row.index:
            value = row[key]
            if value is not None and not (isinstance(value, float) and math.isnan(value)):
                extra[key] = value.item() if hasattr(value, "item") else value
    return json.dumps(extra, default=str)


def normalize_source_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Map a Hugging Face-like table to canonical columns. Does not persist."""
    if frame is None or frame.empty:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    name_col = _first_present(frame, _NAME_ALIASES)
    location_col = _first_present(frame, _LOCATION_ALIASES)
    if name_col is None or location_col is None:
        raise IngestError("Source data must include name and location columns")

    city_col = _first_present(frame, _CITY_ALIASES)
    cuisine_col = _first_present(frame, _CUISINE_ALIASES)
    rating_col = _first_present(frame, _RATING_ALIASES)
    cost_col = _first_present(frame, _COST_ALIASES)
    address_col = _first_present(frame, _ADDRESS_ALIASES)

    records: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        name = _clean_text(row[name_col])
        location = _clean_text(row[location_col])
        if name is None or location is None:
            continue
        address = _clean_text(row[address_col]) if address_col else None
        explicit_city = _clean_text(row[city_col]) if city_col else None
        city = infer_city(address, location, explicit_city)
        rating = parse_rating(row[rating_col]) if rating_col else None
        cost = parse_cost(row[cost_col]) if cost_col else None
        cuisines = parse_cuisines(row[cuisine_col]) if cuisine_col else []
        records.append(
            {
                "id": make_id(name, address, location),
                "name": name,
                "location": location,
                "city": city,
                "cuisines": cuisines,
                "rating": rating,
                "cost": cost,
                "budget_band": None,
                "extra": _row_extra(row),
            }
        )

    catalog = pd.DataFrame.from_records(records, columns=CANONICAL_COLUMNS)
    return catalog.reset_index(drop=True)


def apply_budget_bands(catalog: pd.DataFrame, override: str | None = None) -> tuple[pd.DataFrame, tuple[float, float] | None]:
    out = catalog.copy()
    cutoffs = compute_budget_cutoffs(out["cost"] if "cost" in out.columns else pd.Series(dtype=float), override)
    if out.empty:
        return out, cutoffs
    out["budget_band"] = [assign_budget_band(cost, cutoffs) for cost in out["cost"]]
    return out, cutoffs
