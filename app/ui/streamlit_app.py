"""Preference form and recommendation cards (filter + LLM / fallback)."""

from __future__ import annotations

import streamlit as st

from app.api.schemas import RecommendRequest
from app.data.catalog import CatalogNotLoadedError, load_catalog
from app.data.meta import build_catalog_meta
from app.recommend.service import recommend

st.set_page_config(page_title="Restaurant recommender", layout="centered")
st.title("Restaurant recommender")
st.caption(
    "Structured filters run on the local catalog first. The model ranks the shortlist "
    "and writes explanations without inventing restaurants. If the model fails, "
    "you still get catalog-backed cards ranked by rating."
)

try:
    catalog = load_catalog()
    meta = build_catalog_meta(catalog)
except CatalogNotLoadedError as exc:
    st.error(str(exc))
    st.stop()

default_location = "Banashankari"
if meta["locations"] and default_location not in meta["locations"]:
    default_location = meta["locations"][0]
default_cuisine = "Italian"
if meta["cuisines"] and default_cuisine not in meta["cuisines"]:
    default_cuisine = meta["cuisines"][0]

location_options = meta["locations"] or [default_location]
cuisine_options = meta["cuisines"] or [default_cuisine]

with st.form("preferences"):
    location = st.selectbox(
        "Location",
        options=location_options,
        index=location_options.index(default_location)
        if default_location in location_options
        else 0,
        help="Neighborhood or city from the catalog (`GET /meta`).",
    )
    budget = st.selectbox("Budget", options=["low", "medium", "high"], index=1)
    if meta["budget_cutoffs"]:
        st.caption(
            "Budget bands use cost for two: "
            f"low ≤ {meta['budget_cutoffs']['low_max']:.0f}; "
            f"medium ≤ {meta['budget_cutoffs']['medium_max']:.0f}; "
            "above that is high."
        )
    cuisine = st.selectbox(
        "Cuisine",
        options=cuisine_options,
        index=cuisine_options.index(default_cuisine)
        if default_cuisine in cuisine_options
        else 0,
    )
    min_rating = st.number_input(
        "Minimum rating",
        min_value=0.0,
        max_value=5.0,
        value=4.0,
        step=0.1,
    )
    notes = st.text_input(
        "Additional notes (optional)",
        value="family-friendly",
        help="Used by the LLM for ranking/copy; not applied as a structured filter.",
    )
    top_k = st.number_input("How many results", min_value=1, max_value=10, value=3, step=1)
    submitted = st.form_submit_button("Find restaurants")

if not submitted:
    st.stop()

try:
    request = RecommendRequest(
        location=location,
        budget=budget,
        cuisine=cuisine,
        min_rating=float(min_rating),
        notes=notes or None,
        top_k=int(top_k),
    )
except Exception as exc:
    st.error(f"Invalid preferences: {exc}")
    st.stop()

response = recommend(catalog, request)

if response.status == "no_matches":
    st.warning(response.hint or "No restaurants matched your filters.")
    st.stop()

if response.source == "fallback":
    st.info(
        "Showing rule-based rankings from the filtered catalog "
        "(the language model was unavailable or returned unusable results)."
    )
elif response.source:
    st.caption(f"Source: {response.source}")

if response.summary:
    st.write(response.summary)

for item in response.recommendations:
    cuisine_text = ", ".join(item.cuisines) if item.cuisines else "—"
    rating_text = "—" if item.rating is None else str(item.rating)
    cost_text = (
        "—"
        if item.cost is None
        else str(int(item.cost) if float(item.cost).is_integer() else item.cost)
    )
    st.subheader(f"{item.rank}. {item.name}")
    st.write(f"**Cuisine:** {cuisine_text}")
    st.write(f"**Rating:** {rating_text}")
    st.write(f"**Estimated cost (for two):** {cost_text}")
    st.write(f"**Location:** {item.location}")
    st.write(item.explanation)
    st.divider()
