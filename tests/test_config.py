"""Config helpers used for deploy (CORS, paths)."""

from __future__ import annotations

from app.config import parse_cors_origins


def test_parse_cors_origins_empty() -> None:
    assert parse_cors_origins("") == []
    assert parse_cors_origins("   ") == []


def test_parse_cors_origins_splits_and_strips() -> None:
    assert parse_cors_origins(
        "https://app.vercel.app, http://localhost:3000 ,https://api.example.com"
    ) == [
        "https://app.vercel.app",
        "http://localhost:3000",
        "https://api.example.com",
    ]
