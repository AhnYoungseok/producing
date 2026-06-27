from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyze, composer, library, patterns, projects, research, songs, youtube
from app.core.config import settings
from app.db.database import init_database
from app.db.database import SQLiteStore
from app.services.auto_reference_batch_worker import start_auto_reference_batch_worker, stop_auto_reference_batch_worker


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    configured_origins = [origin.strip() for origin in (settings.frontend_origins or "").split(",") if origin.strip()]
    frontend_origins = sorted({settings.frontend_origin, *configured_origins, "http://localhost:3100", "http://127.0.0.1:3100"})
    app.add_middleware(
        CORSMiddleware,
        allow_origins=frontend_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    init_database(settings.database_path)
    batch_store = SQLiteStore(settings.database_path)
    app.add_event_handler(
        "startup",
        lambda: start_auto_reference_batch_worker(
            batch_store,
            settings.export_path,
            enabled=settings.auto_reference_batch_enabled,
            interval_seconds=settings.auto_reference_batch_interval_seconds,
            batch_size=settings.auto_reference_batch_size,
            run_on_startup=settings.auto_reference_batch_run_on_startup,
        ),
    )
    app.add_event_handler("shutdown", stop_auto_reference_batch_worker)
    app.include_router(songs.router, prefix="/api")
    app.include_router(analyze.router, prefix="/api")
    app.include_router(library.router, prefix="/api")
    app.include_router(patterns.router, prefix="/api")
    app.include_router(projects.router, prefix="/api")
    app.include_router(composer.router, prefix="/api")
    app.include_router(youtube.router, prefix="/api")
    app.include_router(research.router, prefix="/api")

    @app.get("/api/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
