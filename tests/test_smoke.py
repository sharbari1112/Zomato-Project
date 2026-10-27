"""Phase 0: package imports resolve."""


def test_import_app() -> None:
    import app

    assert app.__version__


def test_import_phase0_stubs() -> None:
    from app.api import schemas
    from app.data import catalog, ingest
    from app.recommend import filters

    assert schemas.RecommendRequest is not None
    assert callable(ingest.ingest)
    assert callable(catalog.load_catalog)
    assert callable(filters.filter_restaurants)
