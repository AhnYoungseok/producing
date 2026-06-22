from __future__ import annotations

import csv
import json
import re
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


EXPORT_COLUMNS = [
    "song_id",
    "title",
    "artist",
    "genre",
    "country",
    "release_year",
    "bpm",
    "bpm_confidence",
    "key",
    "key_confidence",
    "youtube_url",
    "youtube_title",
    "youtube_channel",
    "youtube_duration",
    "youtube_published_date",
    "youtube_view_count",
    "video_type",
    "analysis_source",
    "hook_type",
    "hook_confidence",
    "lyric_theme",
    "lyric_theme_confidence",
    "mood_tags",
    "chorus_progression",
    "song_structure",
    "first_chorus_time",
    "chorus_peak_position",
    "arrangement_build",
    "vocal_tone",
    "mixing_vocal_position",
    "hit_factor",
    "transferable_principles",
    "avoid_copying",
    "created_at",
    "updated_at",
]


def export_store_snapshot(store: Any, export_root: Path) -> dict[str, Any]:
    songs = store.list_songs()
    analyses = store.get_analyses_for_songs([song["id"] for song in songs])
    return export_library_by_genre(songs, analyses, export_root)


def export_library_by_genre(songs: list[dict[str, Any]], analyses: list[dict[str, Any]], export_root: Path) -> dict[str, Any]:
    export_root.mkdir(parents=True, exist_ok=True)
    by_genre_dir = export_root / "by_genre"
    if by_genre_dir.exists():
        shutil.rmtree(by_genre_dir)
    by_genre_dir.mkdir(parents=True, exist_ok=True)

    analysis_by_song_id = {analysis["song_id"]: analysis for analysis in analyses}
    rows = [_build_export_row(song, analysis_by_song_id.get(song["id"])) for song in songs]
    rows.sort(key=lambda row: (row["genre"], row["artist"], row["title"]))

    files: list[str] = []
    all_csv = export_root / "all_songs.csv"
    all_json = export_root / "all_songs.json"
    _write_csv(all_csv, rows)
    _write_json(all_json, rows)
    files.extend([str(all_csv), str(all_json)])

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["genre"] or "Unknown"].append(row)

    index_rows = []
    for genre, genre_rows in sorted(grouped.items(), key=lambda item: item[0].lower()):
        slug = safe_filename(genre)
        genre_csv = by_genre_dir / f"{slug}.csv"
        genre_json = by_genre_dir / f"{slug}.json"
        _write_csv(genre_csv, genre_rows)
        _write_json(genre_json, genre_rows)
        files.extend([str(genre_csv), str(genre_json)])
        index_rows.append(
            {
                "genre": genre,
                "song_count": len(genre_rows),
                "average_bpm": _average([_to_float(row["bpm"]) for row in genre_rows if row["bpm"] != ""]),
                "top_key": _top_value(row["key"] for row in genre_rows),
                "top_hook_type": _top_value(row["hook_type"] for row in genre_rows),
                "csv_path": str(genre_csv),
                "json_path": str(genre_json),
            }
        )

    genre_index_csv = export_root / "genre_index.csv"
    genre_index_json = export_root / "genre_index.json"
    _write_csv(genre_index_csv, index_rows)
    _write_json(genre_index_json, index_rows)
    files.extend([str(genre_index_csv), str(genre_index_json)])

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "export_root": str(export_root),
        "total_songs": len(rows),
        "genre_count": len(index_rows),
        "files": files,
        "spreadsheet_note": "CSV files are encoded as UTF-8 with BOM so Korean text opens cleanly in Excel.",
    }
    manifest_path = export_root / "export_manifest.json"
    _write_json(manifest_path, manifest)
    files.append(str(manifest_path))
    manifest["files"] = files
    return manifest


def _build_export_row(song: dict[str, Any], analysis: dict[str, Any] | None) -> dict[str, Any]:
    analysis = analysis or {}
    concept = analysis.get("concept", {})
    lyrics = analysis.get("lyrics", {})
    structure = analysis.get("structure", {})
    harmony = analysis.get("harmony", {})
    melody = analysis.get("melody", {})
    hook = analysis.get("hook", {})
    arrangement = analysis.get("arrangement", {})
    vocal = analysis.get("vocal", {})
    mixing = analysis.get("mixing", {})
    hit_factor = analysis.get("hit_factor", {})
    takeaway = analysis.get("takeaway", {})
    audio_features = analysis.get("audio_features", {})
    youtube_metadata = song.get("youtube_metadata") or {}
    research_profile = song.get("research_profile") or {}
    musical_features = research_profile.get("musical_features", {})
    identification = research_profile.get("identification", {})

    bpm_field = musical_features.get("bpm", {})
    key_field = musical_features.get("key", {})
    hook_field = musical_features.get("hook_type", {})
    lyric_field = musical_features.get("lyric_theme", {})

    genre = song.get("genre") or concept.get("genre") or _confidence_value(identification.get("genre")) or "Unknown"
    return {
        "song_id": song.get("id"),
        "title": song.get("title") or "",
        "artist": song.get("artist") or "",
        "genre": genre,
        "country": song.get("country") or "",
        "release_year": song.get("release_year") or "",
        "bpm": song.get("bpm") if song.get("bpm") is not None else "",
        "bpm_confidence": bpm_field.get("confidence", "high" if song.get("file_name") and song.get("bpm") is not None else ""),
        "key": song.get("key") or "",
        "key_confidence": key_field.get("confidence", "high" if song.get("file_name") and song.get("key") else ""),
        "youtube_url": song.get("youtube_url") or "",
        "youtube_title": youtube_metadata.get("title") or "",
        "youtube_channel": youtube_metadata.get("channel_name") or "",
        "youtube_duration": youtube_metadata.get("duration") or "",
        "youtube_published_date": youtube_metadata.get("published_date") or "",
        "youtube_view_count": youtube_metadata.get("view_count") or "",
        "video_type": _confidence_value(identification.get("video_type")) or "",
        "analysis_source": audio_features.get("analysis_source") or ("user_uploaded_audio" if song.get("file_name") else "metadata_user_input_research"),
        "hook_type": hook.get("primary_hook_type") or _confidence_value(hook_field) or "",
        "hook_confidence": hook_field.get("confidence", ""),
        "lyric_theme": lyrics.get("lyric_theme") or _confidence_value(lyric_field) or "",
        "lyric_theme_confidence": lyric_field.get("confidence", ""),
        "mood_tags": _join_values(concept.get("mood") or _confidence_value(musical_features.get("mood_tags"))),
        "chorus_progression": harmony.get("chorus_progression") or "",
        "song_structure": _join_values(structure.get("structure"), separator=" - "),
        "first_chorus_time": structure.get("first_chorus_time") if structure.get("first_chorus_time") is not None else "",
        "chorus_peak_position": melody.get("chorus_peak_position") or "",
        "arrangement_build": arrangement.get("arrangement_build") or "",
        "vocal_tone": vocal.get("vocal_tone") or "",
        "mixing_vocal_position": mixing.get("vocal_position") or "",
        "hit_factor": hit_factor.get("main_hit_factor") or "",
        "transferable_principles": _join_values(takeaway.get("transferable_principles")),
        "avoid_copying": _join_values(takeaway.get("avoid_copying")),
        "created_at": song.get("created_at") or "",
        "updated_at": song.get("updated_at") or "",
    }


def safe_filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\\\|?*]+', "_", value.strip())
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = cleaned.strip("._")
    return cleaned or "Unknown"


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = EXPORT_COLUMNS if path.name != "genre_index.csv" else ["genre", "song_count", "average_bpm", "top_key", "top_hook_type", "csv_path", "json_path"]
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _join_values(value: Any, separator: str = "; ") -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return separator.join(str(item) for item in value if item not in (None, ""))
    return str(value)


def _confidence_value(field: Any) -> Any:
    if isinstance(field, dict):
        return field.get("value")
    return field


def _average(values: list[float]) -> str:
    return str(round(mean(values), 2)) if values else ""


def _top_value(values: Any) -> str:
    counts: dict[str, int] = {}
    for value in values:
        if value in (None, ""):
            continue
        counts[str(value)] = counts.get(str(value), 0) + 1
    if not counts:
        return ""
    return sorted(counts.items(), key=lambda item: item[1], reverse=True)[0][0]


def _to_float(value: Any) -> float:
    return float(value)
