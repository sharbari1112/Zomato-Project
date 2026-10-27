"""Application entry: FastAPI with catalog loaded at startup + PlateMatch UI."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import SERVE_UI, parse_cors_origins
from app.data.catalog import CatalogNotLoadedError, load_catalog

WEB_DIR = Path(__file__).resolve().parent / "ui" / "web"


def load_catalog_into_state(app: FastAPI) -> None:
    try:
        app.state.catalog = load_catalog()
        app.state.catalog_error = None
    except CatalogNotLoadedError as exc:
        app.state.catalog = None
        app.state.catalog_error = str(exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_catalog_into_state(app)
    yield


app = FastAPI(
    title="Restaurant recommendation service",
    version="0.1.0",
    lifespan=lifespan,
)

cors_origins = parse_cors_origins()
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

app.include_router(router)

if SERVE_UI and WEB_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")

    @app.get("/")
    def plate_match_ui() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")
