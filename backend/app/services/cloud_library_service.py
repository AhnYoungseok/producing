from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.services.statistics_service import build_hit_song_statistics


DEFAULT_LEDGER_URL = "https://raw.githubusercontent.com/AhnYoungseok/producing/main/cloud_ledger/song_library.json"
SPREADSHEET_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def cloud_library_enabled() -> bool:
    return settings.cloud_library_source.casefold() in {"google_sheet", "sheet", "cloud_ledger", "ledger"}


def load_cloud_songs() -> list[dict[str, Any]]:
    source = settings.cloud_library_source.casefold()
    if source in {"google_sheet", "sheet"} and _has_google_credentials():
        return _load_google_sheet_songs()
    return _load_ledger_songs()


def cloud_total_count() -> int:
    source = settings.cloud_library_source.casefold()
    if source in {"google_sheet", "sheet"} and _has_google_credentials():
        return len(load_cloud_songs())
    ledger = _load_ledger()
    return int(ledger.get("total_after_baseline") or len(ledger.get("songs", [])))


def cloud_dashboard() -> dict[str, Any]:
    songs = load_cloud_songs()
    bpms = [float(song["bpm"]) for song in songs if song.get("bpm") is not None]
    analyses = cloud_analyses_for_songs(songs)
    hooks = _counts(analysis["hook"].get("primary_hook_type") for analysis in analyses)
    return {
        "song_count": cloud_total_count(),
        "visible_song_count": len(songs),
        "genre_counts": _counts(song.get("genre") or "Unknown" for song in songs),
        "average_bpm": round(sum(bpms) / len(bpms), 2) if bpms else 0,
        "top_keys": _counts(song.get("key") for song in songs)[:5],
        "top_progressions": _counts(analysis["harmony"].get("chorus_progression") for analysis in analyses)[:5],
        "top_structures": _counts(" - ".join(analysis["structure"].get("structure", [])) for analysis in analyses)[:5],
        "hook_distribution": hooks[:5],
        "recent_songs": songs[:5],
        "active_projects": [],
        "pattern_count": 0,
        "source": settings.cloud_library_source,
    }


def cloud_statistics() -> dict[str, Any]:
    songs = load_cloud_songs()
    analyses = cloud_analyses_for_songs(songs)
    stats = build_hit_song_statistics(songs, analyses)
    stats["summary"]["song_count"] = cloud_total_count()
    stats["summary"]["visible_song_count"] = len(songs)
    stats["source"] = settings.cloud_library_source
    return stats


def cloud_analyses_for_songs(songs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_analysis_from_song(song) for song in songs]


def cloud_hook_summaries() -> dict[str, Any]:
    songs = load_cloud_songs()
    rows = [_hook_summary_from_song(song) for song in songs]
    return {
        "total_count": cloud_total_count(),
        "usable_count": len(rows),
        "rows": rows,
    }


def find_cloud_song(song_id: str) -> dict[str, Any] | None:
    for song in load_cloud_songs():
        if song.get("id") == song_id:
            return song
    return None


def find_cloud_analysis(song_id: str) -> dict[str, Any] | None:
    song = find_cloud_song(song_id)
    return _analysis_from_song(song) if song else None


def _load_ledger_songs() -> list[dict[str, Any]]:
    ledger = _load_ledger()
    return [_song_from_record(row) for row in ledger.get("songs", [])]


def _load_ledger() -> dict[str, Any]:
    url = settings.cloud_ledger_url or DEFAULT_LEDGER_URL
    try:
        with urllib.request.urlopen(url, timeout=12) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload)
    except Exception:
        return {"total_after_baseline": 0, "songs": []}


def _load_google_sheet_songs() -> list[dict[str, Any]]:
    service = _build_sheets_service()
    rows = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=settings.google_sheet_id, range="'Song Library'!A:K")
        .execute()
        .get("values", [])
    )
    if not rows:
        return []
    header = [_normalize_header(cell) for cell in rows[0]]
    title_index = header.index("title") if "title" in header else 2 if "addeddate" in header else 1
    artist_index = header.index("artist") if "artist" in header else title_index + 1
    added_index = header.index("addeddate") if "addeddate" in header else None
    field_index = {name: header.index(name) for name in header}
    songs = []
    for row in rows[1:]:
        if len(row) <= max(title_index, artist_index) or not row[title_index]:
            continue
        record = {
            "title": _cell(row, title_index),
            "artist": _cell(row, artist_index),
            "genre": _cell(row, field_index.get("genre")),
            "country": _cell(row, field_index.get("country")),
            "release_year": _cell(row, field_index.get("releaseyear")),
            "bpm": _cell(row, field_index.get("bpm")),
            "key": _cell(row, field_index.get("key")),
            "youtube_url": _cell(row, field_index.get("youtubeurl")),
            "added_date": _cell(row, added_index),
            "source_type": _cell(row, field_index.get("sourcetype")) or "google_sheet",
            "data_confidence": "medium",
        }
        songs.append(_song_from_record(record))
    return songs


def _build_sheets_service() -> Any:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    service_account_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    if service_account_json:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".json") as file:
            file.write(service_account_json)
            service_account_file = file.name
    credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=SPREADSHEET_SCOPES)
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def _has_google_credentials() -> bool:
    return bool(settings.google_sheet_id and (os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON") or os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")))


def _song_from_record(record: dict[str, Any]) -> dict[str, Any]:
    title = str(record.get("title") or "Unknown")
    artist = str(record.get("artist") or "Unknown Artist")
    created_at = _date_to_iso(record.get("added_at") or record.get("added_date"))
    research_profile = {
        "profile_type": "cloud_reference_song",
        "lyric_theme": record.get("lyric_theme") or "lyric theme pending",
        "speaker_situation": record.get("speaker_situation") or "",
        "story_flow": record.get("story_flow") or "",
        "hook_type": record.get("hook_type") or "title phrase hook",
        "hook_location": record.get("hook_location") or "chorus",
        "hook_cue": record.get("hook_cue") or title,
        "hook_melody_interval": record.get("hook_melody_interval") or "",
        "hook_melody_rhythm": record.get("hook_melody_rhythm") or "",
        "why_hook_works": record.get("why_hook_works") or "clear title cue and repeatable hook identity",
        "chord_progression": record.get("chord_progression") or "",
        "arrangement": record.get("arrangement") or "",
        "vocal": record.get("vocal") or "",
        "mixing": record.get("mixing") or "",
        "hit_factor": record.get("hit_factor") or "",
        "producer_takeaway": record.get("producer_takeaway") or "",
        "avoid_copying": record.get("avoid_copying") or "Do not copy lyrics, melody, arrangement signature, or artist delivery.",
        "data_confidence": record.get("data_confidence") or "medium",
    }
    return {
        "id": f"cloud_{_identity_hash(title, artist)[:12]}",
        "title": title,
        "artist": artist,
        "genre": record.get("genre") or "Unknown",
        "release_year": _to_int(record.get("release_year")),
        "country": record.get("country") or "",
        "youtube_url": record.get("youtube_url") or "",
        "youtube_metadata": {"source": "reference metadata only", "url": record.get("youtube_url") or ""},
        "research_profile": research_profile,
        "file_name": None,
        "duration": None,
        "bpm": _to_float(record.get("bpm")),
        "key": record.get("key") or "",
        "created_at": created_at,
        "updated_at": record.get("added_at") or created_at,
        "analysis_complete": True,
    }


def _analysis_from_song(song: dict[str, Any]) -> dict[str, Any]:
    profile = song.get("research_profile") or {}
    return {
        "id": f"analysis_{song['id']}",
        "song_id": song["id"],
        "concept": {"mood": profile.get("lyric_theme")},
        "lyrics": {
            "lyric_theme": profile.get("lyric_theme"),
            "core_message": profile.get("story_flow"),
            "title_usage": profile.get("hook_location"),
            "chorus_key_phrase_type": profile.get("hook_type"),
        },
        "structure": {"structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"]},
        "harmony": {"chorus_progression": profile.get("chord_progression")},
        "melody": {
            "hook_melody_intervals": profile.get("hook_melody_interval"),
            "hook_melody_rhythm": profile.get("hook_melody_rhythm"),
        },
        "hook": {
            "primary_hook_type": profile.get("hook_type"),
            "hook_location": profile.get("hook_location"),
            "short_hook_cue": profile.get("hook_cue"),
            "why_hook_works": profile.get("why_hook_works"),
        },
        "rhythm": {},
        "arrangement": {"arrangement_build": profile.get("arrangement")},
        "vocal": {"treatment": profile.get("vocal")},
        "mixing": {"features": profile.get("mixing")},
        "hit_factor": {"factors": [profile.get("hit_factor")] if profile.get("hit_factor") else []},
        "takeaway": {"transferable_principles": [profile.get("producer_takeaway")] if profile.get("producer_takeaway") else []},
        "full_report": {},
        "audio_features": {},
        "created_at": song["created_at"],
        "updated_at": song["updated_at"],
    }


def _hook_summary_from_song(song: dict[str, Any]) -> dict[str, Any]:
    profile = song.get("research_profile") or {}
    return {
        "id": song["id"],
        "title": song.get("title") or "Unknown",
        "artist": song.get("artist") or "Unknown Artist",
        "genre": song.get("genre") or "Unknown",
        "created_at": song.get("created_at"),
        "lyric_hook_cue": _safe_cue(profile.get("hook_cue") or song.get("title") or ""),
        "lyric_function": str(profile.get("lyric_theme") or "가사 요약 보강 필요"),
        "hook_type": str(profile.get("hook_type") or "hook type 보강 필요"),
        "hook_location": str(profile.get("hook_location") or "후크 위치 보강 필요"),
        "interval_pattern": str(profile.get("hook_melody_interval") or "멜로디 간격 보강 필요"),
        "rhythm_pattern": str(profile.get("hook_melody_rhythm") or "멜로디 리듬 보강 필요"),
        "contour": "",
        "lyrics_status": "자동 전문 저장 없음",
        "lyrics_url": f"https://www.google.com/search?q={urllib.parse.quote_plus((song.get('artist') or '') + ' ' + (song.get('title') or '') + ' official lyrics')}",
        "why_it_works": str(profile.get("why_hook_works") or "프로듀서 해석 보강 필요"),
        "confidence": str(profile.get("data_confidence") or "medium"),
    }


def _counts(values: Any) -> list[dict[str, Any]]:
    counter = Counter(str(value) for value in values if value)
    return [{"label": key, "count": value} for key, value in counter.most_common()]


def _identity_hash(title: Any, artist: Any) -> str:
    return hashlib.sha256(f"{_normalize(title)}\0{_normalize_artist(artist)}".encode("utf-8")).hexdigest()


def _normalize(value: Any) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", str(value or "").casefold())


def _normalize_artist(value: Any) -> str:
    text = re.sub(r"\b(feat\.?|ft\.?|with)\b.*$", " ", str(value or "").casefold())
    return re.sub(r"[^0-9a-z가-힣]+", "", text)


def _normalize_header(value: Any) -> str:
    return re.sub(r"[^0-9a-z]+", "", str(value or "").casefold())


def _cell(row: list[Any], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return str(row[index])


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _date_to_iso(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return datetime.now(timezone.utc).isoformat()
    if "T" in text:
        return text
    for fmt in ("%Y.%m.%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            pass
    return text


def _safe_cue(text: str) -> str:
    words = " ".join(str(text).split()).split(" ")
    return " ".join(words[:10])
