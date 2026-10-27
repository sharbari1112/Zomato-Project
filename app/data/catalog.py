"""Read the local catalog store. Does not call Hugging Face."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.config import catalog_file
from app.data.transform import CANONICAL_COLUMNS, IngestError


class CatalogNotLoadedError(IngestError):
    """Raised when the local catalog file is missing or unreadable."""


def catalog_exists(path: str | Path | None = None) -> bool:
    return catalog_file(path).is_file()


def load_catalog(path: str | Path | None = None) -> pd.DataFrame:
    dest = catalog_file(path)
    if not dest.is_file():
        raise CatalogNotLoadedError(
            f"Catalog not found at {dest}. Run `python -m app.data.ingest` first."
        )
    try:
        frame = pd.read_parquet(dest)
    except Exception as exc:
        raise CatalogNotLoadedError(f"Catalog at {dest} could not be read") from exc
    missing = [col for col in CANONICAL_COLUMNS if col not in frame.columns]
    if missing:
        raise CatalogNotLoadedError(f"Catalog at {dest} is missing columns: {missing}")
    return frame
