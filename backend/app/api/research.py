from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.db.database import SQLiteStore, make_id
from app.services.genre_bestseller_service import (
    import_bulk_research_seeds,
    import_genre_bestsellers,
    supported_bestseller_genres,
)
from app.services.auto_reference_batch_worker import auto_batch_status, run_auto_batch_now
from app.services.hit_song_researcher import build_analysis_from_research_profile, build_hit_song_research_profile
from app.services.library_exporter import export_store_snapshot
from app.services.reference_batch_importer import import_next_reference_batch

router = APIRouter()
store = SQLiteStore(settings.database_path)


class YouTubeResearchRequest(BaseModel):
    youtube_url: str
    title: str | None = None
    artist: str | None = None
    genre: str | None = None
    country: str | None = None
    release_year: int | None = None
    lyrics_text: str | None = None
    chord_progression: str | None = None
    analysis_notes: str | None = None


class GenreBestsellerImportRequest(BaseModel):
    genre: str
    limit: int = 10


class BulkResearchSeedImportRequest(BaseModel):
    target_count: int = 1000
    batch_size: int = 1000


class NextReferenceBatchRequest(BaseModel):
    limit: int = 10


@router.post("/research/youtube")
def research_youtube_song(payload: YouTubeResearchRequest) -> dict[str, Any]:
    profile = build_hit_song_research_profile(
        youtube_url=payload.youtube_url,
        lyrics_text=payload.lyrics_text,
        chord_progression=payload.chord_progression,
        analysis_notes=payload.analysis_notes,
        title_hint=payload.title,
        artist_hint=payload.artist,
        genre_hint=payload.genre,
        country_hint=payload.country,
        release_year_hint=payload.release_year,
    )
    identification = profile["identification"]
    features = profile["musical_features"]
    song_id = make_id("song")
    song = store.create_song(
        {
            "id": song_id,
            "title": identification["title"]["value"] or "Untitled Reference",
            "artist": identification["artist"]["value"],
            "genre": identification["genre"]["value"],
            "release_year": identification["release_year"]["value"],
            "country": identification["country"]["value"],
            "youtube_url": profile["youtube_metadata"]["url"],
            "youtube_metadata": profile["youtube_metadata"],
            "research_profile": profile,
            "duration": None,
            "bpm": features["bpm"]["value"],
            "key": features["key"]["value"],
            "file_name": None,
        }
    )
    analysis = build_analysis_from_research_profile(profile)
    saved_analysis = store.save_analysis(song["id"], analysis)
    export_store_snapshot(store, settings.export_path)
    return {"song": store.get_song(song["id"]), "analysis": saved_analysis, "research_profile": profile}


@router.get("/research/genre-bestsellers")
def list_genre_bestseller_catalog() -> dict[str, Any]:
    return {
        "genres": supported_bestseller_genres(),
        "policy": (
            "MVP에서는 큐레이션된 장르별 대표 히트곡 seed를 사용합니다. "
            "YouTube는 레퍼런스 검색/메타데이터 시작점일 뿐 오디오는 다운로드하거나 추출하지 않습니다."
        ),
    }


@router.post("/research/genre-bestsellers")
def import_genre_bestseller_research(payload: GenreBestsellerImportRequest) -> dict[str, Any]:
    try:
        result = import_genre_bestsellers(store, payload.genre, payload.limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    export_store_snapshot(store, settings.export_path)
    return result


@router.post("/research/next-reference-batch")
def import_next_reference_batch_research(payload: NextReferenceBatchRequest) -> dict[str, Any]:
    result = import_next_reference_batch(store, payload.limit)
    if result["imported_count"] == 0:
        raise HTTPException(status_code=409, detail=result["message"])
    result["export_manifest"] = export_store_snapshot(store, settings.export_path)
    return result


@router.get("/research/auto-batch/status")
def get_auto_reference_batch_status() -> dict[str, Any]:
    return auto_batch_status()


@router.post("/research/auto-batch/run-now")
async def run_auto_reference_batch(payload: NextReferenceBatchRequest) -> dict[str, Any]:
    result = await run_auto_batch_now(store, settings.export_path, payload.limit)
    if result["imported_count"] == 0:
        raise HTTPException(status_code=409, detail=result["message"])
    result["export_manifest"] = export_store_snapshot(store, settings.export_path)
    return result


@router.post("/research/bulk-seeds")
def import_bulk_seed_research(payload: BulkResearchSeedImportRequest) -> dict[str, Any]:
    result = import_bulk_research_seeds(store, payload.target_count, payload.batch_size)
    export_store_snapshot(store, settings.export_path)
    return result
