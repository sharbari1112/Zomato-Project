"""Load the Hugging Face Zomato dataset, normalize it, and persist a local catalog."""

from __future__ import annotations

import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Callable

import pandas as pd

from app.config import BUDGET_CUTOFFS, CATALOG_PATH, HF_DATASET_ID, MIN_CATALOG_ROWS, PROJECT_ROOT, catalog_file
from app.data.transform import IngestError, apply_budget_bands, normalize_source_frame

logger = logging.getLogger(__name__)

INGEST_NOTES_PATH = PROJECT_ROOT / "data" / "INGEST.md"


def load_huggingface_frame(dataset_id: str) -> pd.DataFrame:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise IngestError("The 'datasets' package is required to download the catalog") from exc
    try:
        dataset = load_dataset(dataset_id, split="train")
    except Exception as exc:
        raise IngestError(
            f"Could not load Hugging Face dataset '{dataset_id}'. "
            "Check the network connection and HF_DATASET_ID."
        ) from exc
    frame = dataset.to_pandas()
    if frame is None or frame.empty:
        raise IngestError(f"Hugging Face dataset '{dataset_id}' returned no rows")
    return frame


def persist_catalog(catalog: pd.DataFrame, path: Path, min_rows: int = 1) -> Path:
    if catalog is None or catalog.empty:
        raise IngestError("Refusing to persist an empty catalog")
    if len(catalog) < min_rows:
        raise IngestError(
            f"Catalog has {len(catalog)} rows; need at least {min_rows}. "
            "Not writing the local file."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    catalog.to_parquet(tmp, index=False)
    tmp.replace(path)
    logger.info("Wrote %s rows to %s", len(catalog), path)
    return path


def _top_counts(values: list[str], limit: int = 15) -> list[tuple[str, int]]:
    return Counter(values).most_common(limit)


def write_ingest_notes(
    catalog: pd.DataFrame,
    cutoffs: tuple[float, float] | None,
    dataset_id: str,
    path: Path = INGEST_NOTES_PATH,
) -> None:
    locations = [str(v) for v in catalog["location"].dropna().tolist()]
    cities = [str(v) for v in catalog["city"].dropna().tolist()]
    cuisine_tokens: list[str] = []
    for item in catalog["cuisines"].tolist():
        if item is None:
            continue
        if isinstance(item, str):
            cuisine_tokens.extend(part.strip() for part in item.split(",") if part.strip())
            continue
        try:
            cuisine_tokens.extend(str(part).strip() for part in list(item) if str(part).strip())
        except TypeError:
            text = str(item).strip()
            if text:
                cuisine_tokens.append(text)
    costs = pd.to_numeric(catalog["cost"], errors="coerce")
    cutoff_line = (
        f"low <= {cutoffs[0]:.2f}; medium <= {cutoffs[1]:.2f}; above that is high"
        if cutoffs
        else "not computed (no numeric costs)"
    )
    lines = [
        "# Catalog ingest notes",
        "",
        f"Source: `{dataset_id}`",
        "",
        "This Hugging Face dump is **Bangalore** Zomato listings (neighborhoods such as Banashankari,",
        "not a multi-city India dump). Prefer UI examples that exist in the tables below — e.g.",
        "`Bangalore` (city), `Banashankari` / `Indiranagar` / `Koramangala` (location),",
        "`Italian` / `Chinese` / `North Indian` (cuisine).",
        "",
        "## Last ingest",
        "",
        f"- Rows: **{len(catalog)}**",
        f"- Budget cutoffs (cost for two): {cutoff_line}",
        f"- Cost min / median / max: {costs.min()} / {costs.median()} / {costs.max()}",
        f"- Rows with rating: {int(catalog['rating'].notna().sum())}",
        f"- Rows with cost: {int(catalog['cost'].notna().sum())}",
        "",
        "### Top cities",
        "",
    ]
    for name, count in _top_counts(cities):
        lines.append(f"- {name}: {count}")
    lines.extend(["", "### Top locations", ""])
    for name, count in _top_counts(locations):
        lines.append(f"- {name}: {count}")
    lines.extend(["", "### Top cuisines", ""])
    for name, count in _top_counts(cuisine_tokens):
        lines.append(f"- {name}: {count}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def ingest(
    *,
    dataset_id: str | None = None,
    dest: str | Path | None = None,
    budget_cutoffs_override: str | None = None,
    min_rows: int | None = None,
    source_loader: Callable[[str], pd.DataFrame] | None = None,
    write_notes: bool = True,
) -> Path:
    """Download (unless a loader is injected), normalize, and write the catalog.

    Does not run on ordinary API requests. Call explicitly via `python -m app.data.ingest`.
    """
    dataset_id = dataset_id or HF_DATASET_ID
    dest_path = catalog_file(dest if dest is not None else CATALOG_PATH)
    override = BUDGET_CUTOFFS if budget_cutoffs_override is None else budget_cutoffs_override
    min_rows = MIN_CATALOG_ROWS if min_rows is None else min_rows
    loader = source_loader or load_huggingface_frame

    logger.info("Loading dataset %s", dataset_id)
    source = loader(dataset_id)
    catalog = normalize_source_frame(source)
    logger.info(
        "Normalized %s source rows to %s catalog rows (dropped missing name/location)",
        len(source),
        len(catalog),
    )
    catalog, cutoffs = apply_budget_bands(catalog, override)
    persist_catalog(catalog, dest_path, min_rows=min_rows)
    if write_notes:
        write_ingest_notes(catalog, cutoffs, dataset_id)
    return dest_path


def main(argv: list[str] | None = None) -> int:
    del argv  # reserved for future flags
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        path = ingest()
    except IngestError as exc:
        logger.error("%s", exc)
        print(f"Ingest failed: {exc}", file=sys.stderr)
        return 1
    print(f"Catalog written to {path}")
    print(f"Ingest notes written to {INGEST_NOTES_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
