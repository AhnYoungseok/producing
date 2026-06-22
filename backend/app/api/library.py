from typing import Any
from urllib.parse import quote_plus

from fastapi import APIRouter

from app.core.config import settings
from app.db.database import SQLiteStore
from app.services.library_exporter import export_store_snapshot
from app.services.statistics_service import build_hit_song_statistics

router = APIRouter()
store = SQLiteStore(settings.database_path)


@router.get("/library/dashboard")
def dashboard() -> dict:
    return store.dashboard()


@router.get("/library/statistics")
def statistics() -> dict:
    songs = store.list_songs()
    analyses = store.get_analyses_for_songs([song["id"] for song in songs])
    return build_hit_song_statistics(songs, analyses)


@router.get("/library/songs")
def library_songs() -> dict:
    return {"songs": store.list_songs()}


@router.get("/library/hook-summaries")
def hook_summaries() -> dict[str, Any]:
    songs = store.list_songs()
    analyses = {analysis["song_id"]: analysis for analysis in store.get_analyses_for_songs([song["id"] for song in songs])}
    rows = [_build_hook_summary(song, analyses.get(song["id"])) for song in songs]
    usable_count = sum(1 for row in rows if row["confidence"] != "insufficient")
    return {
        "total_count": len(songs),
        "usable_count": usable_count,
        "rows": rows,
    }


@router.post("/library/export")
def export_library() -> dict:
    return export_store_snapshot(store, settings.export_path)


def _build_hook_summary(song: dict[str, Any], analysis: dict[str, Any] | None) -> dict[str, Any]:
    lyrics = _as_dict((analysis or {}).get("lyrics"))
    hook = _as_dict((analysis or {}).get("hook"))
    melody = _as_dict((analysis or {}).get("melody"))
    profile = _as_dict(song.get("research_profile"))
    user_inputs = _as_dict(profile.get("user_inputs"))
    has_user_lyrics = bool(str(user_inputs.get("lyrics_text") or "").strip())
    lyric_candidates = hook.get("lyric_hook_candidates")
    first_lyric_candidate = str(lyric_candidates[0]) if isinstance(lyric_candidates, list) and lyric_candidates else ""
    raw_cue = first_lyric_candidate or _value(hook.get("short_hook_cue")) or _value(hook.get("hook_cue")) or str(song.get("title") or "")
    confidence = _hook_confidence(hook, melody, analysis)
    return {
        "id": song["id"],
        "title": song.get("title") or "Unknown",
        "artist": song.get("artist") or "Unknown Artist",
        "genre": song.get("genre") or "Unknown",
        "created_at": song.get("created_at"),
        "lyric_hook_cue": _normalize_lyric_cue(raw_cue, str(song.get("title") or "")),
        "lyric_function": _value(lyrics.get("lyric_theme")) or _value(lyrics.get("core_message")) or "가사 요약 보강 필요",
        "hook_type": _value(hook.get("primary_hook_type")) or _value(lyrics.get("chorus_key_phrase_type")) or "hook type 보강 필요",
        "hook_location": _value(hook.get("hook_location")) or "후크 위치 보강 필요",
        "interval_pattern": _value(melody.get("hook_melody_intervals")) or _value(melody.get("interval_style")) or "멜로디 간격 보강 필요",
        "rhythm_pattern": _value(melody.get("hook_melody_rhythm")) or _value(melody.get("melody_rhythm")) or "멜로디 리듬 보강 필요",
        "contour": _value(melody.get("hook_melody_contour")) or _value(melody.get("hook_melody_shape")) or _value(melody.get("motif_type")),
        "lyrics_status": "사용자 제공 실제 가사 있음" if has_user_lyrics else "자동 전문 저장 없음",
        "lyrics_url": _official_lyrics_search_url(song),
        "why_it_works": _value(hook.get("why_hook_works")) or _value(melody.get("creative_principle")) or "프로듀서 해석 보강 필요",
        "confidence": confidence,
    }


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _value(input_value: Any) -> str:
    if input_value is None or input_value == "":
        return ""
    if isinstance(input_value, list):
        return ", ".join(filter(None, (_value(item) for item in input_value)))
    if isinstance(input_value, dict):
        value = input_value.get("value")
        if value is not None:
            return _value(value)
        return str(input_value)
    return str(input_value)


def _normalize_lyric_cue(cue: str, title: str) -> str:
    lowered = cue.lower()
    if not cue or any(token in lowered for token in ["cue", "form", "motif", "image", "riff"]):
        return _safe_lyric_excerpt(title)
    return _safe_lyric_excerpt(cue)


def _safe_lyric_excerpt(text: str) -> str:
    words = " ".join(text.split()).split(" ")
    if len(words) <= 10:
        return " ".join(words)
    return f"{' '.join(words[:10])}..."


def _hook_confidence(hook: dict[str, Any], melody: dict[str, Any], analysis: dict[str, Any] | None) -> str:
    if not analysis:
        return "insufficient"
    hook_confidence = _as_dict(_as_dict(hook.get("data_confidence")).get("primary_hook_type")).get("confidence")
    melody_confidence = _as_dict(_as_dict(melody.get("data_confidence")).get("melody")).get("confidence")
    return _value(hook_confidence) or _value(melody_confidence) or "medium"


def _official_lyrics_search_url(song: dict[str, Any]) -> str:
    query = f"{song.get('artist') or ''} {song.get('title') or ''} official lyrics"
    return f"https://www.google.com/search?q={quote_plus(query)}"
