from __future__ import annotations

import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.db.database import SQLiteStore


SPREADSHEET_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DEFAULT_SHEET_ID = "1U_WUMnel9AZv-7YymqMRMDw5iX_MI-M3r2Yw0e7umNs"
SYNC_TABS = [
    "Song Library",
    "전체 곡명",
    "전체 곡명 Raw",
    "Dashboard",
    "Statistics",
    "Genre Summary",
    "[차트1] 장르별 곡 수 분포",
    "연동 검증",
]


def sync_google_sheet_from_store(store: SQLiteStore, *, sheet_id: str | None = None) -> dict[str, Any]:
    if not _credentials_configured():
        return {"status": "skipped", "reason": "GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_FILE is not set"}

    try:
        service = _build_sheets_service()
    except ModuleNotFoundError as exc:
        return {"status": "skipped", "reason": f"missing Google Sheets dependency: {exc.name}"}

    songs = _load_songs(store)
    stats = _build_stats(songs)
    spreadsheet_id = sheet_id or _env_value("GOOGLE_SHEET_ID") or DEFAULT_SHEET_ID
    date_label = _today_label()
    required_tabs = [*SYNC_TABS, f"{date_label} 추천 정보"]

    metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_ids = _ensure_sheets(service, spreadsheet_id, metadata, required_tabs)
    _resize_sheets(service, spreadsheet_id, sheet_ids, row_count=max(400, len(songs) + 40))

    value_updates = [
        _value_update("Song Library", "A1:J", _song_library_rows(songs)),
        _value_update("전체 곡명", "A1:J", [["=FILTER('Song Library'!A:J,LEN('Song Library'!A:A))"]]),
        _value_update("전체 곡명 Raw", "A1:J", [["=FILTER('Song Library'!A:J,LEN('Song Library'!A:A))"]]),
        _value_update("Dashboard", "A1:F40", _dashboard_rows(stats)),
        _value_update("Statistics", "A1:D100", _statistics_rows(stats)),
        _value_update("Genre Summary", "A1:F100", _genre_summary_rows(songs)),
        _value_update("[차트1] 장르별 곡 수 분포", "A1:B100", [["Genre", "Songs"], *stats["genre_counts"][:80]]),
        _value_update("연동 검증", "A1:D30", _validation_rows(stats)),
        _value_update(f"{date_label} 추천 정보", "A1:F30", _recommendation_rows(stats, date_label)),
    ]
    clear_ranges = [update["range"] for update in value_updates]
    service.spreadsheets().values().batchClear(spreadsheetId=spreadsheet_id, body={"ranges": clear_ranges}).execute()
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"valueInputOption": "USER_ENTERED", "data": value_updates},
    ).execute()
    return {
        "status": "synced",
        "spreadsheet_id": spreadsheet_id,
        "song_count": len(songs),
        "date_tab": f"{date_label} 추천 정보",
    }


def _credentials_configured() -> bool:
    return bool(_env_value("GOOGLE_SERVICE_ACCOUNT_JSON") or _env_value("GOOGLE_SERVICE_ACCOUNT_FILE"))


def _build_sheets_service() -> Any:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    service_account_json = _env_value("GOOGLE_SERVICE_ACCOUNT_JSON")
    service_account_file = _env_value("GOOGLE_SERVICE_ACCOUNT_FILE")
    if service_account_json:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".json") as file:
            file.write(service_account_json)
            service_account_file = file.name
    service_account_path = _resolve_path(service_account_file)
    credentials = service_account.Credentials.from_service_account_file(service_account_path, scopes=SPREADSHEET_SCOPES)
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def _env_value(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    for dotenv_path in _dotenv_candidates():
        if not dotenv_path.exists():
            continue
        for line in dotenv_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key.strip() == name:
                return value.strip().strip('"').strip("'") or None
    return None


def _dotenv_candidates() -> list[Path]:
    return [
        Path.cwd() / ".env",
        Path.cwd() / "backend" / ".env",
        Path(__file__).resolve().parents[3] / ".env",
        Path(__file__).resolve().parents[3] / "backend" / ".env",
    ]


def _resolve_path(path_value: str | None) -> str:
    if not path_value:
        raise RuntimeError("Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_FILE for Google Sheets updates.")
    path = Path(path_value)
    if path.is_absolute():
        return str(path)
    for base in [Path.cwd(), Path.cwd() / "backend", Path(__file__).resolve().parents[3], Path(__file__).resolve().parents[3] / "backend"]:
        candidate = (base / path).resolve()
        if candidate.exists():
            return str(candidate)
    return str(path.resolve())


def _ensure_sheets(service: Any, spreadsheet_id: str, metadata: dict[str, Any], required: list[str]) -> dict[str, int]:
    existing = {sheet["properties"]["title"]: sheet["properties"]["sheetId"] for sheet in metadata.get("sheets", [])}
    missing = [title for title in required if title not in existing]
    if missing:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": title, "gridProperties": {"rowCount": 400, "columnCount": 12}}}} for title in missing]},
        ).execute()
        metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        existing = {sheet["properties"]["title"]: sheet["properties"]["sheetId"] for sheet in metadata.get("sheets", [])}
    return existing


def _resize_sheets(service: Any, spreadsheet_id: str, sheet_ids: dict[str, int], *, row_count: int) -> None:
    requests = [
        {
            "updateSheetProperties": {
                "properties": {"sheetId": sheet_id, "gridProperties": {"rowCount": row_count, "columnCount": 12, "frozenRowCount": 1}},
                "fields": "gridProperties(rowCount,columnCount,frozenRowCount)",
            }
        }
        for title, sheet_id in sheet_ids.items()
        if title in SYNC_TABS or title.endswith("추천 정보")
    ]
    if requests:
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()


def _load_songs(store: SQLiteStore) -> list[dict[str, Any]]:
    with store._connect() as connection:
        rows = connection.execute(
            """
            SELECT s.*, a.hook_json
            FROM songs s
            LEFT JOIN song_analyses a ON a.song_id = s.id
            ORDER BY s.created_at ASC, s.title COLLATE NOCASE ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _song_library_rows(songs: list[dict[str, Any]]) -> list[list[Any]]:
    rows = [["No", "Added Date", "Title", "Artist", "Genre", "Country", "Release Year", "BPM", "Key", "Source Type"]]
    for index, song in enumerate(songs, start=1):
        rows.append(
            [
                index,
                str(song.get("created_at") or "")[:10],
                song.get("title") or "",
                song.get("artist") or "",
                song.get("genre") or "",
                song.get("country") or "",
                song.get("release_year") or "",
                song.get("bpm") or "",
                song.get("key") or "",
                "local_db_reference",
            ]
        )
    return rows


def _build_stats(songs: list[dict[str, Any]]) -> dict[str, Any]:
    bpms = [float(song["bpm"]) for song in songs if song.get("bpm") is not None]
    hook_counter: Counter[str] = Counter()
    for song in songs:
        try:
            hook_type = json.loads(song.get("hook_json") or "{}").get("primary_hook_type") or "Unknown"
        except json.JSONDecodeError:
            hook_type = "Unknown"
        hook_counter[hook_type] += 1
    return {
        "total": len(songs),
        "average_bpm": round(sum(bpms) / len(bpms), 2) if bpms else 0,
        "bpm_count": len(bpms),
        "missing_bpm": sum(1 for song in songs if song.get("bpm") is None),
        "missing_key": sum(1 for song in songs if not song.get("key")),
        "unique_count": len({(_normalize(song.get("title")), _normalize_artist(song.get("artist"))) for song in songs}),
        "genre_counts": Counter(song.get("genre") or "Unknown" for song in songs).most_common(),
        "country_counts": Counter(song.get("country") or "Unknown" for song in songs).most_common(),
        "key_counts": Counter(song.get("key") for song in songs if song.get("key")).most_common(),
        "hook_counts": hook_counter.most_common(),
        "bpm_buckets": Counter(_bpm_bucket(song.get("bpm")) for song in songs).most_common(),
    }


def _dashboard_rows(stats: dict[str, Any]) -> list[list[Any]]:
    rows = [
        ["Metric", "Value", "Note", "", "Hook Type", "Songs"],
        ["Total Songs", stats["total"], "Synced from local DB"],
        ["Analyzed Songs", stats["total"], "Rows currently present in local Hit Song Lab DB"],
        ["Average BPM", stats["average_bpm"], f"{stats['bpm_count']} rows with BPM values"],
        ["YouTube Policy", "No audio extraction", "Reference metadata only; no YouTube audio download/extraction/analysis"],
        [],
        ["Genre", "Songs", "", "", "Top Hook Type", "Songs"],
    ]
    for index in range(max(len(stats["genre_counts"][:12]), len(stats["hook_counts"][:12]))):
        genre = stats["genre_counts"][index] if index < len(stats["genre_counts"][:12]) else ("", "")
        hook = stats["hook_counts"][index] if index < len(stats["hook_counts"][:12]) else ("", "")
        rows.append([genre[0], genre[1], "", "", hook[0], hook[1]])
    return rows


def _statistics_rows(stats: dict[str, Any]) -> list[list[Any]]:
    rows = [
        ["Section", "Metric", "Value", "Insight"],
        ["Summary", "Total Songs", stats["total"], "Local DB and Song Library row count"],
        ["Summary", "Average BPM", stats["average_bpm"], "Average across rows with BPM"],
        ["Summary", "Rows Missing BPM", stats["missing_bpm"], "Low-confidence or chart-only metadata rows"],
        ["Summary", "Rows Missing Key", stats["missing_key"], "Low-confidence or chart-only metadata rows"],
    ]
    rows += [["BPM Distribution", key, value, "Song count by BPM bucket"] for key, value in stats["bpm_buckets"]]
    rows += [["Top Genres", key, value, "Genre frequency"] for key, value in stats["genre_counts"][:20]]
    rows += [["Top Countries", key, value, "Country frequency"] for key, value in stats["country_counts"][:12]]
    rows += [["Top Keys", key, value, "Key frequency"] for key, value in stats["key_counts"][:12]]
    return rows


def _genre_summary_rows(songs: list[dict[str, Any]]) -> list[list[Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for song in songs:
        grouped[song.get("genre") or "Unknown"].append(song)
    rows = [["Genre", "Average BPM", "Song Count", "Top Key", "Country Mix", "Notes"]]
    for genre, items in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))[:80]:
        bpms = [float(song["bpm"]) for song in items if song.get("bpm") is not None]
        top_key = Counter(song.get("key") for song in items if song.get("key")).most_common(1)
        country_mix = ", ".join(f"{country}:{count}" for country, count in Counter(song.get("country") or "Unknown" for song in items).most_common(3))
        rows.append(
            [
                genre,
                round(sum(bpms) / len(bpms), 2) if bpms else "",
                len(items),
                top_key[0][0] if top_key else "",
                country_mix,
                "synced from local DB",
            ]
        )
    return rows


def _validation_rows(stats: dict[str, Any]) -> list[list[Any]]:
    return [
        ["Validation Item", "Value", "Status", "Description"],
        ["Master rows", stats["total"], "OK", "Song Library synced from local DB"],
        ["Unique title+artist", stats["unique_count"], "CHECK", "Normalized duplicate count can be refined"],
        ["Rows missing BPM", stats["missing_bpm"], "CHECK" if stats["missing_bpm"] else "OK", "BPM missing means low confidence metadata"],
        ["Rows missing Key", stats["missing_key"], "CHECK" if stats["missing_key"] else "OK", "Key missing means low confidence metadata"],
        ["YouTube policy", "OK", "OK", "No YouTube audio download, extraction, capture, conversion, separation, or analysis"],
        ["Last sync", _today_label(), "OK", "Automatic service-account sync"],
    ]


def _recommendation_rows(stats: dict[str, Any], date_label: str) -> list[list[Any]]:
    top_buckets = ", ".join(f"{key}:{value}" for key, value in stats["bpm_buckets"][:3])
    top_genres = ", ".join(f"{key}:{value}" for key, value in stats["genre_counts"][:3])
    return [
        ["Section", "Item", "Recommendation", "Evidence", "Producer Direction", "Guardrail"],
        ["Final Direction", "Date", date_label, f"{stats['total']} accumulated rows", "K-pop/global pop hybrid with compact title hook", "Do not copy melody or lyrics"],
        ["Tempo", "BPM Target", "100-119 or 120-139", f"Top BPM buckets: {top_buckets}", "Start mid-tempo and lift chorus energy", "Use original rhythm"],
        ["Hook", "Hook Type", "title phrase + melodic/rhythm hook", "Top hook patterns from accumulated analysis", "Place the title cue in first chorus bar", "Use short cue only"],
        ["Genre", "Direction", "K-pop dance/pop with global chart polish", f"Top genres: {top_genres}", "Clean verse, sticky pre, high-contrast chorus", "No copyrighted lyric reuse"],
        ["Data", "Low confidence", "Rows missing BPM/key need later refinement", f"BPM missing {stats['missing_bpm']}, key missing {stats['missing_key']}", "Use as trend signal, not exact transcription", "No YouTube audio analysis"],
    ]


def _value_update(sheet: str, cell_range: str, rows: list[list[Any]]) -> dict[str, Any]:
    return {"range": f"'{sheet}'!{cell_range}", "majorDimension": "ROWS", "values": rows}


def _bpm_bucket(value: Any) -> str:
    if value is None:
        return "Unknown"
    bpm = float(value)
    if bpm < 70:
        return "Under 70"
    if bpm < 85:
        return "70-84"
    if bpm < 100:
        return "85-99"
    if bpm < 120:
        return "100-119"
    if bpm < 140:
        return "120-139"
    return "140+"


def _today_label() -> str:
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    return f"{now.year}.{now.month}.{now.day}"


def _normalize(value: Any) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", str(value or "").casefold())


def _normalize_artist(value: Any) -> str:
    text = re.sub(r"\b(feat\.?|ft\.?|with)\b.*$", "", str(value or "").casefold())
    return re.sub(r"[^0-9a-z가-힣]+", "", text)
