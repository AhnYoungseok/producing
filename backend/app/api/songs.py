from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.db.database import SQLiteStore
from app.models.song import SongCreate, SongListResponse, SongResponse
from app.services.cloud_library_service import (
    cloud_library_enabled,
    find_cloud_analysis,
    find_cloud_song,
    load_cloud_songs,
)
from app.services.hit_song_researcher import build_analysis_from_research_profile, build_structured_profile
from app.services.library_exporter import export_store_snapshot

router = APIRouter()
store = SQLiteStore(settings.database_path)


class SongResearchDataUpdate(BaseModel):
    lyrics_text: str | None = None
    chord_progression: str | None = None
    analysis_notes: str | None = None


@router.post("/songs", response_model=SongResponse)
def create_song(payload: SongCreate) -> SongResponse:
    song = store.create_song(payload.model_dump())
    return SongResponse(**song)


@router.get("/songs", response_model=SongListResponse)
def list_songs(
    query: str | None = None,
    genre: str | None = None,
    key: str | None = None,
    country: str | None = None,
    emotion: str | None = None,
) -> SongListResponse:
    if cloud_library_enabled():
        songs = _filter_cloud_songs(load_cloud_songs(), query=query, genre=genre, key=key, country=country)
        return SongListResponse(songs=[SongResponse(**song) for song in songs])
    songs = store.list_songs(query=query, genre=genre, key=key, country=country, emotion=emotion)
    return SongListResponse(songs=[SongResponse(**song) for song in songs])


@router.get("/songs/{song_id}", response_model=SongResponse)
def get_song(song_id: str) -> SongResponse:
    if cloud_library_enabled():
        song = find_cloud_song(song_id)
        if song is None:
            raise HTTPException(status_code=404, detail="곡을 찾을 수 없습니다.")
        return SongResponse(**song)
    song = store.get_song(song_id)
    if song is None:
        raise HTTPException(status_code=404, detail="곡을 찾을 수 없습니다.")
    return SongResponse(**song)


@router.get("/songs/{song_id}/analysis")
def get_song_analysis(song_id: str) -> dict[str, Any]:
    if cloud_library_enabled():
        analysis = find_cloud_analysis(song_id)
        if analysis is None:
            raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
        return analysis
    analysis = store.get_analysis(song_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
    return analysis


@router.post("/songs/{song_id}/research-data")
def update_song_research_data(song_id: str, payload: SongResearchDataUpdate) -> dict[str, Any]:
    song = store.get_song(song_id)
    if song is None:
        raise HTTPException(status_code=404, detail="곡을 찾을 수 없습니다.")
    profile = song.get("research_profile") or {}
    if not profile:
        raise HTTPException(status_code=400, detail="Reference Analysis 프로필이 있는 곡만 업데이트할 수 있습니다.")

    user_inputs = profile.get("user_inputs") or {}
    lyrics_text = payload.lyrics_text if payload.lyrics_text is not None else user_inputs.get("lyrics_text")
    chord_progression = payload.chord_progression if payload.chord_progression is not None else user_inputs.get("chord_progression")
    analysis_notes = payload.analysis_notes if payload.analysis_notes is not None else user_inputs.get("analysis_notes")

    updated_profile = build_structured_profile(
        youtube_metadata=profile.get("youtube_metadata") or song.get("youtube_metadata") or {},
        identification=profile.get("identification") or {},
        public_data=profile.get("external_sources") or {},
        lyrics_text=lyrics_text,
        chord_progression=chord_progression,
        analysis_notes=analysis_notes,
    )
    updated_profile["profile_type"] = profile.get("profile_type") or updated_profile.get("profile_type")
    updated_profile["safe_design_policy"] = profile.get("safe_design_policy") or updated_profile.get("safe_design_policy", {})
    updated_profile["youtube_metadata"] = profile.get("youtube_metadata") or updated_profile.get("youtube_metadata", {})
    updated_profile["external_sources"] = profile.get("external_sources") or updated_profile.get("external_sources", {})
    _preserve_existing_feature_values(updated_profile, profile, ["bpm", "key", "popularity_indicators", "arrangement_notes", "producer_notes"])
    store.update_song_research_profile(song_id, updated_profile)
    analysis = build_analysis_from_research_profile(updated_profile)
    saved_analysis = store.save_analysis(song_id, analysis)
    export_store_snapshot(store, settings.export_path)
    return {"song": store.get_song(song_id), "analysis": saved_analysis, "research_profile": updated_profile}


def _preserve_existing_feature_values(updated_profile: dict[str, Any], previous_profile: dict[str, Any], keys: list[str]) -> None:
    updated_features = updated_profile.setdefault("musical_features", {})
    previous_features = previous_profile.get("musical_features") or {}
    for key in keys:
        current = updated_features.get(key)
        previous = previous_features.get(key)
        if not previous:
            continue
        if not current or (isinstance(current, dict) and current.get("value") in (None, "", [])):
            updated_features[key] = previous


def _filter_cloud_songs(
    songs: list[dict[str, Any]],
    *,
    query: str | None = None,
    genre: str | None = None,
    key: str | None = None,
    country: str | None = None,
) -> list[dict[str, Any]]:
    filtered = songs
    if query:
        needle = query.casefold()
        filtered = [song for song in filtered if needle in str(song.get("title") or "").casefold() or needle in str(song.get("artist") or "").casefold()]
    if genre:
        filtered = [song for song in filtered if song.get("genre") == genre]
    if key:
        filtered = [song for song in filtered if song.get("key") == key]
    if country:
        filtered = [song for song in filtered if song.get("country") == country]
    return filtered
