"""Catalog meta for UI dropdowns must expand Parquet/numpy cuisine arrays."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.data.meta import build_catalog_meta


def test_meta_cuisines_expand_numpy_arrays() -> None:
    catalog = pd.DataFrame(
        [
            {
                "id": "r1",
                "name": "A",
                "location": "Banashankari",
                "city": "Bangalore",
                "cuisines": np.array(["North Indian", "Chinese"], dtype=object),
                "rating": 4.2,
                "cost": 400.0,
                "budget_band": "medium",
                "extra": "{}",
            },
            {
                "id": "r2",
                "name": "B",
                "location": "Indiranagar",
                "city": "Bangalore",
                "cuisines": np.array(["Italian"], dtype=object),
                "rating": 4.5,
                "cost": 550.0,
                "budget_band": "medium",
                "extra": "{}",
            },
        ]
    )
    meta = build_catalog_meta(catalog)
    assert "North Indian" in meta["cuisines"]
    assert "Chinese" in meta["cuisines"]
    assert "Italian" in meta["cuisines"]
    assert not any(name.startswith("[") for name in meta["cuisines"])
