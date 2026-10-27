"""Environment-backed settings. Secrets stay in `.env`, never in git."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


HF_DATASET_ID = _env(
    "HF_DATASET_ID",
    "ManikaSaini/zomato-restaurant-recommendation",
) or "ManikaSaini/zomato-restaurant-recommendation"
CATALOG_PATH = _env("CATALOG_PATH", "data/catalog.parquet") or "data/catalog.parquet"
# Keep shortlist small: each row is prompt tokens against TPM/TPD caps.
SHORTLIST_SIZE = int(_env("SHORTLIST_SIZE", "10") or "10")
DEFAULT_TOP_K = int(_env("DEFAULT_TOP_K", "3") or "3")
BUDGET_CUTOFFS = _env("BUDGET_CUTOFFS")
MIN_CATALOG_ROWS = int(_env("MIN_CATALOG_ROWS", "100") or "100")

# Groq LLM (Phase 4). Prefer LLM_API_KEY; GROQ_API_KEY is also accepted.
LLM_PROVIDER = (_env("LLM_PROVIDER", "groq") or "groq").casefold()
LLM_MODEL = _env("LLM_MODEL", "openai/gpt-oss-120b") or "openai/gpt-oss-120b"
LLM_API_KEY = _env("LLM_API_KEY") or _env("GROQ_API_KEY")
LLM_TEMPERATURE = float(_env("LLM_TEMPERATURE", "0.3") or "0.3")
# Cap completion size so one call cannot eat most of an 8K TPM budget.
LLM_MAX_COMPLETION_TOKENS = int(_env("LLM_MAX_COMPLETION_TOKENS", "350") or "350")
# gpt-oss reasoning tokens count toward TPM; "low" is required on free tiers.
LLM_REASONING_EFFORT = (_env("LLM_REASONING_EFFORT", "low") or "low").casefold()

# Prefer identical preference hashes for a short window (0 disables).
CACHE_TTL_SECONDS = float(_env("CACHE_TTL_SECONDS", "300") or "300")

# Cross-origin UI (Vercel). Comma-separated; empty = no CORS middleware.
CORS_ORIGINS = _env("CORS_ORIGINS", "") or ""

# Serve PlateMatch static UI from FastAPI (local demo). Set false on Render.
SERVE_UI = (_env("SERVE_UI", "true") or "true").casefold() in {
    "1",
    "true",
    "yes",
    "on",
}


def parse_cors_origins(raw: str | None = None) -> list[str]:
    """Split CORS_ORIGINS into a clean origin list."""
    value = CORS_ORIGINS if raw is None else raw
    if not value or not value.strip():
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def catalog_file(raw: str | Path | None = None) -> Path:
    path = Path(raw) if raw is not None else Path(CATALOG_PATH)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path
