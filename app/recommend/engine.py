"""Groq LLM ranking: call, parse, validate IDs, join catalog display fields."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from app.api.schemas import RecommendationItem
from app.config import (
    LLM_API_KEY,
    LLM_MAX_COMPLETION_TOKENS,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_REASONING_EFFORT,
    LLM_TEMPERATURE,
)
from app.recommend.prompts import build_messages, build_repair_user_prompt

CompleteFn = Callable[[list[dict[str, str]]], str]

__all__ = [
    "CompleteFn",
    "EngineError",
    "complete_chat_groq",
    "join_ranked_to_candidates",
    "parse_ranked_payload",
    "rank_shortlist",
]


class EngineError(Exception):
    """LLM call or validation failed after optional repair retry."""


def _preferences_mapping(preferences: Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(preferences, Mapping):
        return {
            "location": preferences.get("location"),
            "budget": preferences.get("budget"),
            "cuisine": preferences.get("cuisine"),
            "min_rating": preferences.get("min_rating"),
            "notes": preferences.get("notes"),
        }
    return {
        "location": getattr(preferences, "location", None),
        "budget": getattr(preferences, "budget", None),
        "cuisine": getattr(preferences, "cuisine", None),
        "min_rating": getattr(preferences, "min_rating", None),
        "notes": getattr(preferences, "notes", None),
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise EngineError("LLM returned an empty response")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            raise EngineError("LLM response was not valid JSON") from None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise EngineError("LLM response was not valid JSON") from exc
    if not isinstance(data, dict):
        raise EngineError("LLM JSON root must be an object")
    return data


def parse_ranked_payload(text: str) -> tuple[str | None, list[dict[str, str]]]:
    """Parse model JSON into (summary, [{id, explanation}, ...])."""
    data = _extract_json_object(text)
    summary = data.get("summary")
    if summary is not None:
        summary = str(summary).strip() or None
    ranked = data.get("ranked_ids")
    if ranked is None:
        raise EngineError("LLM JSON missing ranked_ids")
    if not isinstance(ranked, list):
        raise EngineError("LLM ranked_ids must be a list")

    items: list[dict[str, str]] = []
    for entry in ranked:
        if not isinstance(entry, Mapping):
            continue
        item_id = entry.get("id")
        if item_id is None or str(item_id).strip() == "":
            continue
        explanation = entry.get("explanation")
        items.append(
            {
                "id": str(item_id).strip(),
                "explanation": str(explanation).strip() if explanation is not None else "",
            }
        )
    return summary, items


def _candidate_to_item(
    candidate: Mapping[str, Any],
    rank: int,
    explanation: str,
) -> RecommendationItem:
    cuisines = candidate.get("cuisines") or []
    if not isinstance(cuisines, list):
        cuisines = [str(cuisines)]
    rating = candidate.get("rating")
    cost = candidate.get("cost")
    return RecommendationItem(
        id=str(candidate["id"]),
        rank=rank,
        name=str(candidate["name"]),
        cuisines=[str(c) for c in cuisines],
        rating=float(rating) if rating is not None else None,
        cost=float(cost) if cost is not None else None,
        location=str(candidate.get("location") or ""),
        explanation=explanation or "Selected from the filtered shortlist.",
    )


def join_ranked_to_candidates(
    ranked_ids: Sequence[Mapping[str, str]],
    shortlist: Sequence[Mapping[str, Any]],
    *,
    top_k: int,
) -> list[RecommendationItem]:
    """Drop unknown IDs; display fields always come from the shortlist row."""
    by_id = {str(row["id"]): row for row in shortlist}
    items: list[RecommendationItem] = []
    seen: set[str] = set()
    for entry in ranked_ids:
        item_id = str(entry["id"])
        if item_id in seen or item_id not in by_id:
            continue
        seen.add(item_id)
        items.append(
            _candidate_to_item(
                by_id[item_id],
                rank=len(items) + 1,
                explanation=str(entry.get("explanation") or ""),
            )
        )
        if len(items) >= top_k:
            break
    return items


def complete_chat_groq(messages: list[dict[str, str]]) -> str:
    """Call Groq chat completions; return assistant text."""
    if (LLM_PROVIDER or "").casefold() != "groq":
        raise EngineError(
            f"Unsupported LLM_PROVIDER={LLM_PROVIDER!r}; set LLM_PROVIDER=groq"
        )
    api_key = LLM_API_KEY
    if not api_key:
        raise EngineError(
            "Missing LLM API key. Set LLM_API_KEY or GROQ_API_KEY in .env"
        )

    try:
        from groq import Groq
    except ImportError as exc:
        raise EngineError("groq package is not installed; pip install groq") from exc

    client = Groq(api_key=api_key)
    create_kwargs: dict[str, Any] = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": LLM_TEMPERATURE,
        "response_format": {"type": "json_object"},
        "max_completion_tokens": LLM_MAX_COMPLETION_TOKENS,
    }
    # gpt-oss models support reasoning_effort; low keeps TPM usable on free tiers.
    if "gpt-oss" in (LLM_MODEL or "").casefold() and LLM_REASONING_EFFORT:
        create_kwargs["reasoning_effort"] = LLM_REASONING_EFFORT

    try:
        response = client.chat.completions.create(**create_kwargs)
    except Exception as exc:  # noqa: BLE001 — retried once, then fallback in service
        raise EngineError(f"Groq request failed: {exc}") from exc

    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        raise EngineError("Groq response missing message content") from exc
    if content is None or not str(content).strip():
        raise EngineError("LLM returned an empty response")
    return content


def _is_retriable(exc: EngineError) -> bool:
    """Timeout / provider / malformed JSON are retried once; invalid IDs are not."""
    message = str(exc).casefold()
    non_retriable = (
        "no ids that exist",
        "cannot rank an empty",
        "top_k must be",
    )
    return not any(token in message for token in non_retriable)


def rank_shortlist(
    shortlist: Sequence[Mapping[str, Any]],
    preferences: Mapping[str, Any] | Any,
    top_k: int,
    *,
    complete: CompleteFn | None = None,
) -> tuple[str | None, list[RecommendationItem]]:
    """Rank a non-empty shortlist with the LLM and join catalog fields.

    One repair retry on timeout or malformed JSON. Unknown IDs are stripped.
    Raises EngineError if the call fails after retry or no valid IDs remain
    (the service layer then uses deterministic fallback).
    """
    if not shortlist:
        raise EngineError("Cannot rank an empty shortlist")
    if top_k < 1:
        raise EngineError("top_k must be >= 1")

    prefs = _preferences_mapping(preferences)
    messages = build_messages(prefs, shortlist, top_k)
    complete_fn = complete or complete_chat_groq
    last_error: EngineError | None = None

    for attempt in range(2):
        try:
            raw = complete_fn(messages)
            summary, ranked = parse_ranked_payload(raw)
            items = join_ranked_to_candidates(ranked, shortlist, top_k=top_k)
            if not items:
                raise EngineError("LLM returned no IDs that exist in the shortlist")
            return summary, items
        except EngineError as exc:
            last_error = exc
            if attempt == 0 and _is_retriable(exc):
                # Lean repair: system + ids/prefs only (no full candidate dump again).
                messages = [
                    {"role": "system", "content": messages[0]["content"]},
                    {
                        "role": "user",
                        "content": build_repair_user_prompt(prefs, shortlist, top_k),
                    },
                ]
                continue
            raise

    assert last_error is not None
    raise last_error
