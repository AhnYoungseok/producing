from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.db.database import SQLiteStore
from app.services.google_sheet_sync_service import sync_google_sheet_from_store
from app.services.library_exporter import export_store_snapshot
from app.services.reference_batch_importer import import_next_reference_batch


_task: asyncio.Task[None] | None = None
_lock = asyncio.Lock()
_state: dict[str, Any] = {
    "enabled": False,
    "running": False,
    "interval_seconds": 600,
    "batch_size": 10,
    "last_run_at": None,
    "next_run_at": None,
    "last_result": None,
    "last_error": None,
}


def auto_batch_status() -> dict[str, Any]:
    return dict(_state)


def start_auto_reference_batch_worker(
    store: SQLiteStore,
    export_path: Path,
    *,
    enabled: bool,
    interval_seconds: int,
    batch_size: int,
    run_on_startup: bool,
) -> None:
    global _task
    _state.update(
        {
            "enabled": enabled,
            "interval_seconds": interval_seconds,
            "batch_size": batch_size,
        }
    )
    if not enabled or (_task and not _task.done()):
        return
    _task = asyncio.create_task(_worker_loop(store, export_path, interval_seconds, batch_size, run_on_startup))


async def stop_auto_reference_batch_worker() -> None:
    global _task
    _state["enabled"] = False
    if not _task:
        return
    _task.cancel()
    try:
        await _task
    except asyncio.CancelledError:
        pass
    _task = None


async def run_auto_batch_now(store: SQLiteStore, export_path: Path, batch_size: int | None = None) -> dict[str, Any]:
    size = batch_size or int(_state.get("batch_size") or 10)
    async with _lock:
        _state["running"] = True
        _state["last_error"] = None
        try:
            result = await asyncio.to_thread(import_next_reference_batch, store, size)
            if result.get("imported_count", 0) > 0:
                await asyncio.to_thread(export_store_snapshot, store, export_path)
                result["google_sheet_sync"] = await asyncio.to_thread(sync_google_sheet_from_store, store)
            now = _now()
            _state["last_run_at"] = now.isoformat()
            _state["last_result"] = _summarize_result(result)
            return result
        except Exception as exc:
            _state["last_error"] = str(exc)
            raise
        finally:
            _state["running"] = False


async def _worker_loop(
    store: SQLiteStore,
    export_path: Path,
    interval_seconds: int,
    batch_size: int,
    run_on_startup: bool,
) -> None:
    if run_on_startup:
        await run_auto_batch_now(store, export_path, batch_size)
    while _state.get("enabled"):
        next_run = _now() + timedelta(seconds=interval_seconds)
        _state["next_run_at"] = next_run.isoformat()
        await asyncio.sleep(interval_seconds)
        if not _state.get("enabled"):
            break
        await run_auto_batch_now(store, export_path, batch_size)


def _summarize_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "imported_count": result.get("imported_count", 0),
        "created_count": result.get("created_count", 0),
        "total_after": result.get("total_after", 0),
        "queue_remaining": result.get("queue_remaining", 0),
        "songs": [
            {
                "id": song.get("id"),
                "title": song.get("title"),
                "artist": song.get("artist"),
                "genre": song.get("genre"),
            }
            for song in result.get("songs", [])
        ],
        "google_sheet_sync": result.get("google_sheet_sync"),
        "message": result.get("message"),
    }


def _now() -> datetime:
    return datetime.now(timezone.utc)
