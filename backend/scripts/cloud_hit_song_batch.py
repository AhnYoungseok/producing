from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SPREADSHEET_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DEFAULT_SHEET_ID = "1U_WUMnel9AZv-7YymqMRMDw5iX_MI-M3r2Yw0e7umNs"
ROOT_DIR = Path(__file__).resolve().parents[2]
QUEUE_PATH = ROOT_DIR / "backend" / "seeds" / "cloud_reference_queue.json"
FALLBACK_QUEUE_PATH = ROOT_DIR / "backend" / "seeds" / "cloud_reference_fallback_hits.json"
LEDGER_PATH = ROOT_DIR / "cloud_ledger" / "song_library.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Add safe reference-song research rows to a Google Sheet.")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--sheet-id", default=os.environ.get("GOOGLE_SHEET_ID") or DEFAULT_SHEET_ID)
    parser.add_argument("--ledger-path", default=str(LEDGER_PATH))
    parser.add_argument("--date", default=datetime.now().strftime("%Y.%-m.%-d") if os.name != "nt" else _windows_date())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    queue = _load_candidate_pool()
    ledger_path = Path(args.ledger_path)
    ledger = _load_ledger(ledger_path)
    ledger_records = ledger.get("songs", [])

    service = None
    existing_rows = []
    google_sheet_status = "skipped: Google credentials are not set"
    if not args.dry_run and _has_google_credentials():
        service = _build_sheets_service()
        existing_rows = _read_values(service, args.sheet_id, "'Song Library'!A:K")
        google_sheet_status = "ready"

    existing_keys = _existing_song_keys(existing_rows) | _record_keys(ledger_records)
    existing_hashes = set(ledger.get("baseline", {}).get("identity_hashes", []))
    existing_hashes |= {_identity_hash(row.get("title"), row.get("artist")) for row in ledger_records}
    selected = _select_unique(queue, existing_keys, existing_hashes, args.batch_size)

    if len(selected) != args.batch_size:
        raise SystemExit(
            f"Need exactly {args.batch_size} unique songs, but only found {len(selected)}. "
            "Add more real songs to backend/seeds/cloud_reference_queue.json."
        )

    now_iso = datetime.now().isoformat(timespec="seconds")
    selected = [_ledger_song(row, args.date, now_iso) for row in selected]
    merged_ledger_records = ledger_records + selected
    baseline_count = int(ledger.get("baseline", {}).get("count") or len(existing_hashes))
    total_after_ledger = baseline_count + len(merged_ledger_records)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "selected": [f"{row['title']} - {row['artist']}" for row in selected],
                    "ledger_total_after": total_after_ledger,
                    "google_sheet_status": "dry_run",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    _save_ledger(
        ledger_path,
        {
            **ledger,
            "version": 1,
            "updated_at": now_iso,
            "total_after_baseline": total_after_ledger,
            "songs": merged_ledger_records,
        },
    )

    sheet_added_count = 0
    if service is not None:
        sheet_meta = service.spreadsheets().get(spreadsheetId=args.sheet_id).execute()
        _ensure_sheets(
            service,
            args.sheet_id,
            sheet_meta,
            [
                "전체 곡명 Raw",
                "후크 멜로디 리듬 Raw",
                "Chord Lyrics Raw",
                "Producer Features Raw",
                "연동 검증",
                args.date + " 추천 정보",
            ],
        )
        existing_count = _data_row_count(existing_rows)
        sheet_existing_keys = _existing_song_keys(existing_rows)
        missing_for_sheet = [row for row in merged_ledger_records if _record_key(row) not in sheet_existing_keys]
        sheet_added_count = len(missing_for_sheet)
        start_index = existing_count + 1

        merged_rows = _dedupe_records(_existing_song_records(existing_rows) + missing_for_sheet)
        stats = _build_stats(merged_rows)
        updates = []
        if missing_for_sheet:
            updates.extend(_value_update("Song Library", f"A{start_index + 1}:K{start_index + len(missing_for_sheet)}", _song_library_rows(missing_for_sheet, start_index)))
            updates.extend(_value_update("전체 곡명 Raw", f"A{start_index + 1}:I{start_index + len(missing_for_sheet)}", _all_title_rows(missing_for_sheet, start_index)))
            updates.extend(_value_update("후크 멜로디 리듬 Raw", f"A{start_index + 1}:M{start_index + len(missing_for_sheet)}", _hook_rows(missing_for_sheet, start_index)))
            updates.extend(_value_update("Chord Lyrics Raw", f"A{start_index + 1}:L{start_index + len(missing_for_sheet)}", _chord_lyric_rows(missing_for_sheet)))
            updates.extend(_value_update("Producer Features Raw", f"A{start_index + 1}:J{start_index + len(missing_for_sheet)}", _producer_rows(missing_for_sheet)))
        updates.extend(_value_update("Dashboard", "A1:F18", _dashboard_rows(stats, selected, args.date)))
        updates.extend(_value_update("Statistics", "A1:D30", _statistics_rows(stats)))
        updates.extend(_value_update("Genre Summary", "A1:F80", _genre_summary_rows(merged_rows)))
        updates.extend(_value_update("[차트1] 장르별 곡 수 분포", "A1:B80", [["Genre", "Songs"], *stats["genre_counts"]]))
        updates.extend(_value_update("Pattern Summaries", "A1:E12", _pattern_rows(stats)))
        updates.extend(_value_update("연동 검증", "A1:D11", _validation_rows(stats)))
        updates.extend(_value_update(args.date + " 추천 정보", "A1:F24", _recommendation_rows(stats, args.date)))

        body = {"valueInputOption": "USER_ENTERED", "data": updates}
        service.spreadsheets().values().batchUpdate(spreadsheetId=args.sheet_id, body=body).execute()
        google_sheet_status = "updated" if sheet_added_count else "up_to_date"

    print(
        json.dumps(
            {
                "added": [f"{row['title']} - {row['artist']}" for row in selected],
                "ledger_total_after": total_after_ledger,
                "ledger_path": _display_path(ledger_path),
                "google_sheet_status": google_sheet_status,
                "google_sheet_added_rows": sheet_added_count,
                "low_confidence": [
                    f"{row['title']} - {row['artist']}: {row.get('data_confidence')}"
                    for row in selected
                    if row.get("data_confidence") in {"low", "medium-low"}
                ],
                "youtube_policy": "YouTube reference metadata only. No YouTube audio download, extraction, capture, conversion, separation, or analysis.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _build_sheets_service() -> Any:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    service_account_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    if service_account_json:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".json") as file:
            file.write(service_account_json)
            service_account_file = file.name
    if not service_account_file:
        raise RuntimeError("Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_FILE for cloud Google Sheets updates.")
    credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=SPREADSHEET_SCOPES)
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def _has_google_credentials() -> bool:
    return bool(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON") or os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE"))


def _load_candidate_pool() -> list[dict[str, Any]]:
    queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    if FALLBACK_QUEUE_PATH.exists():
        queue.extend(json.loads(FALLBACK_QUEUE_PATH.read_text(encoding="utf-8")))
    return queue


def _load_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "baseline": {"count": 0, "identity_hashes": []}, "songs": []}
    ledger = json.loads(path.read_text(encoding="utf-8"))
    ledger.setdefault("version", 1)
    ledger.setdefault("baseline", {"count": 0, "identity_hashes": []})
    ledger.setdefault("songs", [])
    return ledger


def _save_ledger(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def _read_values(service: Any, spreadsheet_id: str, range_name: str) -> list[list[Any]]:
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    return result.get("values", [])


def _ensure_sheets(service: Any, spreadsheet_id: str, metadata: dict[str, Any], required: list[str]) -> dict[str, int]:
    existing = {sheet["properties"]["title"]: sheet["properties"]["sheetId"] for sheet in metadata.get("sheets", [])}
    missing = [title for title in required if title not in existing]
    if missing:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": title, "gridProperties": {"rowCount": 500, "columnCount": 12}}}} for title in missing]},
        ).execute()
        metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        existing = {sheet["properties"]["title"]: sheet["properties"]["sheetId"] for sheet in metadata.get("sheets", [])}
    return existing


def _existing_song_keys(rows: list[list[Any]]) -> set[tuple[str, str]]:
    title_index, artist_index = _song_library_title_artist_indices(rows)
    keys = set()
    for row in rows[1:]:
        if len(row) <= max(title_index, artist_index):
            continue
        keys.add((_normalize(row[title_index]), _normalize_artist(row[artist_index])))
    return keys


def _existing_song_records(rows: list[list[Any]]) -> list[dict[str, Any]]:
    title_index, artist_index = _song_library_title_artist_indices(rows)
    offset = 1 if title_index == 2 else 0
    records = []
    for row in rows[1:]:
        if len(row) <= max(title_index, artist_index):
            continue
        records.append(
            {
                "added_date": row[1] if offset and len(row) > 1 else "",
                "title": row[title_index] if len(row) > title_index else "",
                "artist": row[artist_index] if len(row) > artist_index else "",
                "genre": row[3 + offset] if len(row) > 3 + offset else "Unknown",
                "country": row[4 + offset] if len(row) > 4 + offset else "",
                "release_year": row[5 + offset] if len(row) > 5 + offset else "",
                "bpm": _to_float(row[6 + offset] if len(row) > 6 + offset else None),
                "key": row[7 + offset] if len(row) > 7 + offset else "",
                "hook_type": "",
                "chord_progression": "",
                "data_confidence": "medium",
            }
        )
    return records


def _song_library_title_artist_indices(rows: list[list[Any]]) -> tuple[int, int]:
    if rows:
        header = [_normalize_header(cell) for cell in rows[0]]
        if "addeddate" in header:
            return 2, 3
    return 1, 2


def _record_key(row: dict[str, Any]) -> tuple[str, str]:
    return (_normalize(row.get("title")), _normalize_artist(row.get("artist")))


def _record_keys(rows: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {_record_key(row) for row in rows if row.get("title")}


def _identity_hash(title: Any, artist: Any) -> str:
    key = f"{_normalize(title)}\0{_normalize_artist(artist)}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _ledger_song(row: dict[str, Any], added_date: str, added_at: str) -> dict[str, Any]:
    return {
        **row,
        "added_date": added_date,
        "added_at": added_at,
        "source_type": "github_actions_cloud_reference",
    }


def _dedupe_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    deduped = []
    for row in rows:
        key = _record_key(row)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _select_unique(
    queue: list[dict[str, Any]],
    existing_keys: set[tuple[str, str]],
    existing_hashes: set[str],
    batch_size: int,
) -> list[dict[str, Any]]:
    selected = []
    selected_keys = set()
    for row in queue:
        key = (_normalize(row.get("title")), _normalize_artist(row.get("artist")))
        identity_hash = _identity_hash(row.get("title"), row.get("artist"))
        if key in existing_keys or key in selected_keys or identity_hash in existing_hashes:
            continue
        selected.append(row)
        selected_keys.add(key)
        if len(selected) == batch_size:
            break
    return selected


def _data_row_count(rows: list[list[Any]]) -> int:
    title_index, _ = _song_library_title_artist_indices(rows)
    return max(0, sum(1 for row in rows[1:] if len(row) > title_index and row[title_index]))


def _song_library_rows(songs: list[dict[str, Any]], start_index: int) -> list[list[Any]]:
    return [
        [
            start_index + i,
            song.get("added_date", ""),
            song["title"],
            song["artist"],
            song["genre"],
            song["country"],
            song["release_year"],
            song["bpm"],
            song["key"],
            song.get("source_type", "cloud_curated_reference"),
            "cloud batch, unique real hit, no YouTube audio extraction",
        ]
        for i, song in enumerate(songs)
    ]


def _all_title_rows(songs: list[dict[str, Any]], start_index: int) -> list[list[Any]]:
    return [
        [
            start_index + i,
            song["title"],
            song["artist"],
            song["genre"],
            song["country"],
            song["release_year"],
            song["bpm"],
            song["key"],
            song["youtube_url"],
        ]
        for i, song in enumerate(songs)
    ]


def _hook_rows(songs: list[dict[str, Any]], start_index: int) -> list[list[Any]]:
    return [
        [
            start_index + i,
            song["title"],
            song["artist"],
            song["hook_location"],
            song["hook_melody_interval"],
            song["hook_cue"],
            song["hook_melody_rhythm"],
            "medium",
            song["why_hook_works"],
            song["producer_takeaway"],
            song["data_confidence"],
            "curated public music research; no YouTube audio extraction",
            "전체 멜로디 채보 아님",
        ]
        for i, song in enumerate(songs)
    ]


def _chord_lyric_rows(songs: list[dict[str, Any]]) -> list[list[Any]]:
    return [
        [
            song["title"],
            song["artist"],
            song["lyric_theme"],
            song["speaker_situation"],
            song["story_flow"],
            song["hook_type"],
            song["hook_location"],
            song["hook_cue"],
            song["why_hook_works"],
            song["chord_progression"],
            song["data_confidence"],
            "가사 원문 저장 없음, YouTube 오디오 분석 없음",
        ]
        for song in songs
    ]


def _producer_rows(songs: list[dict[str, Any]]) -> list[list[Any]]:
    return [
        [
            song["title"],
            song["genre"],
            song["lyric_theme"],
            song["story_flow"],
            song["arrangement"],
            song["vocal"],
            song["mixing"],
            song["hit_factor"],
            song["producer_takeaway"],
            song["avoid_copying"],
        ]
        for song in songs
    ]


def _build_stats(songs: list[dict[str, Any]]) -> dict[str, Any]:
    bpms = [float(song["bpm"]) for song in songs if _to_float(song.get("bpm")) is not None]
    genre_counter = Counter(song.get("genre") or "Unknown" for song in songs)
    key_counter = Counter(song.get("key") for song in songs if song.get("key"))
    chord_counter = Counter(song.get("chord_progression") for song in songs if song.get("chord_progression"))
    hook_counter = Counter(song.get("hook_type") for song in songs if song.get("hook_type"))
    bpm_buckets = Counter(_bpm_bucket(song.get("bpm")) for song in songs)
    identity_keys = {(_normalize(song.get("title")), _normalize_artist(song.get("artist"))) for song in songs if song.get("title")}
    missing_bpm_key = sum(1 for song in songs if not song.get("bpm") or not song.get("key"))
    missing_research_fields = sum(
        1
        for song in songs
        if not song.get("lyric_theme") or not song.get("hook_type") or not song.get("chord_progression")
    )
    low_confidence_count = sum(1 for song in songs if str(song.get("data_confidence") or "").lower() in {"low", "medium-low"})
    return {
        "total": len(songs),
        "unique_count": len(identity_keys),
        "missing_bpm_key": missing_bpm_key,
        "missing_research_fields": missing_research_fields,
        "low_confidence_count": low_confidence_count,
        "average_bpm": round(sum(bpms) / len(bpms), 2) if bpms else 0,
        "genre_counts": genre_counter.most_common(),
        "key_counts": key_counter.most_common(8),
        "chord_counts": chord_counter.most_common(8),
        "hook_counts": hook_counter.most_common(8),
        "bpm_buckets": bpm_buckets.most_common(),
    }


def _dashboard_rows(stats: dict[str, Any], selected: list[dict[str, Any]], date_label: str) -> list[list[Any]]:
    rows = [
        ["Metric", "Value", "Note", "", "Hook Type", "Songs"],
        ["Total Songs", stats["total"], "Google Sheet cloud ledger"],
        ["Analyzed Songs", stats["total"], "Rows with structured reference research"],
        ["Average BPM", stats["average_bpm"], "Across accumulated reference library"],
        ["Last Batch", f"{date_label} / {len(selected)} songs", ", ".join(song["title"] for song in selected)],
        ["YouTube Policy", "No audio extraction", "Reference metadata/research only"],
        [],
        ["Genre", "Songs", "", "", "Top Hooks", ""],
    ]
    for i in range(max(len(stats["genre_counts"][:10]), len(stats["hook_counts"][:10]))):
        genre = stats["genre_counts"][i] if i < len(stats["genre_counts"][:10]) else ("", "")
        hook = stats["hook_counts"][i] if i < len(stats["hook_counts"][:10]) else ("", "")
        rows.append([genre[0], genre[1], "", "", hook[0], hook[1]])
    return rows


def _statistics_rows(stats: dict[str, Any]) -> list[list[Any]]:
    rows = [
        ["Section", "Metric", "Value", "Insight"],
        ["Summary", "Total Songs", stats["total"], "Current cloud sheet ledger"],
        ["Summary", "Average BPM", stats["average_bpm"], "Average BPM across accumulated references"],
    ]
    rows += [["BPM Distribution", key, value, "Song count by BPM bucket"] for key, value in stats["bpm_buckets"]]
    rows += [["Top Keys", key, value, "Key frequency"] for key, value in stats["key_counts"]]
    rows += [["Top Progressions", key, value, "Chord progression frequency"] for key, value in stats["chord_counts"]]
    rows += [["Top Hooks", key, value, "Hook type frequency"] for key, value in stats["hook_counts"]]
    return rows


def _genre_summary_rows(songs: list[dict[str, Any]]) -> list[list[Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for song in songs:
        grouped[song.get("genre") or "Unknown"].append(song)
    rows = [["Genre", "Average BPM", "Song Count", "Top Hook Type", "Top Chorus Progression", "Notes"]]
    for genre, items in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        bpms = [float(song["bpm"]) for song in items if _to_float(song.get("bpm")) is not None]
        top_hook = Counter(song.get("hook_type") for song in items if song.get("hook_type")).most_common(1)
        top_chord = Counter(song.get("chord_progression") for song in items if song.get("chord_progression")).most_common(1)
        rows.append(
            [
                genre,
                round(sum(bpms) / len(bpms), 2) if bpms else "",
                len(items),
                top_hook[0][0] if top_hook else "",
                top_chord[0][0] if top_chord else "",
                "cloud sheet accumulated summary",
            ]
        )
    return rows


def _pattern_rows(stats: dict[str, Any]) -> list[list[Any]]:
    top_bpm_bucket = stats["bpm_buckets"][0] if stats["bpm_buckets"] else ("Unknown", 0)
    top_hook = stats["hook_counts"][0] if stats["hook_counts"] else ("Unknown", 0)
    return [
        ["ID", "Title", "Summary", "Producer Takeaway", "Confidence"],
        ["tempo_center", "Tempo Center", f"현재 누적 평균 BPM은 약 {stats['average_bpm']}입니다.", "장르별 중심 BPM 주변에서 보컬 호흡과 그루브를 먼저 설계하세요.", "medium"],
        ["bpm_distribution", "BPM Distribution", f"가장 많은 BPM 구간은 {top_bpm_bucket[0]}입니다.", "트렌디한 팝은 통계의 중심 구간에서 시작한 뒤 콘셉트에 맞게 변형합니다.", "medium"],
        ["hook_design", "Hook Design", f"가장 많이 보이는 후크 유형은 {top_hook[0]}입니다.", "후렴 첫 두 마디에는 제목 단서, 반복 리듬, 좁은 음역 모티브 중 하나를 명확히 배치하세요.", "medium"],
        ["copyright_safe", "Copyright-Safe Research", "저장 데이터는 원문 가사나 YouTube 오디오가 아니라 요약/연구 필드입니다.", "새 곡에는 감정 기능과 구조 원리만 일반화해서 적용하세요.", "high"],
    ]


def _validation_rows(stats: dict[str, Any]) -> list[list[Any]]:
    duplicate_count = max(0, stats["total"] - stats["unique_count"])
    status = "OK" if duplicate_count == 0 else "중복 수정 필요"
    return [
        ["검증 항목", "값", "상태", "설명"],
        ["Master rows", stats["total"], "OK" if stats["total"] > 0 else "확인 필요", "Song Library 기준 누적 곡 수"],
        ["Unique title+artist", stats["unique_count"], "OK" if duplicate_count == 0 else "중복 확인 필요", "정규화된 곡명+아티스트 기준"],
        ["Duplicate count", duplicate_count, status, "0이어야 함"],
        ["Missing BPM/key", stats["missing_bpm_key"], "OK" if stats["missing_bpm_key"] == 0 else "저신뢰/누락 있음", "BPM 또는 Key 누락 검사"],
        ["Missing lyric/hook/chord", stats["missing_research_fields"], "OK" if stats["missing_research_fields"] == 0 else "보강 필요", "가사 주제, 후크 유형, 코드 진행 누락 검사"],
        ["Low confidence rows", stats["low_confidence_count"], "OK" if stats["low_confidence_count"] == 0 else "저신뢰 항목 있음", "low/medium-low 신뢰도 항목"],
        ["YouTube policy", "OK", "OK", "YouTube 오디오는 다운로드/추출/분리/변환/분석하지 않음"],
        ["Raw tab policy", "OK", "OK", "자동 배치는 Raw 탭에만 쓰고 보이는 탭은 공식으로 연동"],
        ["Last sync source", "cloud batch", "OK", "GitHub Actions 또는 로컬 배치에서 갱신"],
    ]


def _recommendation_rows(stats: dict[str, Any], date_label: str) -> list[list[Any]]:
    top_bpm_bucket = stats["bpm_buckets"][0][0] if stats["bpm_buckets"] else "100-119"
    top_key = stats["key_counts"][0][0] if stats["key_counts"] else "G major"
    top_chord = stats["chord_counts"][0][0] if stats["chord_counts"] else "I - V - vi - IV"
    top_hook = stats["hook_counts"][0][0] if stats["hook_counts"] else "lyric + melody hook"
    return [
        ["섹션", "항목", "추천 정보", "Hit Song Lab 통계 근거", "트렌드/창작 해석", "제작 지시"],
        ["최종 추천", "추천 날짜", date_label, f"누적 {stats['total']}곡 기준", "날짜별 1개 추천 탭", "같은 날짜 탭은 새로 만들지 말고 갱신"],
        ["최종 추천", "곡 방향", "K-pop emotional pop + global groove + short title hook", f"평균 BPM {stats['average_bpm']}, 최다 BPM 구간 {top_bpm_bucket}", "짧은 제목 후크와 반복 가능한 리듬이 현재 데이터에서 강함", "제목은 2-4단어 또는 4-8음절로 압축"],
        ["기본 정보", "BPM", top_bpm_bucket, "누적 BPM 분포 최다 구간", "스트리밍에서는 반복 청취 가능한 미드템포가 유리", "Verse는 여백, Chorus는 리듬 밀도 상승"],
        ["기본 정보", "Key 후보", top_key, "누적 Key 최빈값", "보컬 음역에 맞춰 전조 없이 안정 설계", "후렴 최고음 위치를 먼저 정하고 Key 조정"],
        ["화성", "추천 코드 진행", top_chord, "누적 코드 진행 최빈값", "익숙한 진행 위에 사운드와 후크를 새롭게 설계", "진행 자체보다 후렴 첫 마디의 열림/닫힘을 결정"],
        ["후크", "후크 유형", top_hook, "누적 후크 유형 최빈값", "후렴 첫 두 마디의 기억 장치가 중요", "제목 단서 + 반복 리듬 + 좁은 음역 모티브"],
        ["가사", "가사 방향", "일상 이미지 하나로 감정을 압축하는 회상형/자기회복형 서사", "가사 원문이 아니라 테마/화자/상황 데이터를 통계화", "원곡 문장 금지, 새 장면과 새 문장으로 작성"],
        ["편곡", "편곡 방향", "초반 절제, 후렴 리듬 개방, 마지막 후렴 레이어 확장", "K-pop/Global pop 누적 패턴", "첫 10초 안에 사운드 정체성 제시"],
        ["정책", "YouTube 사용", "reference metadata only", "YouTube 오디오 다운로드/추출/분석 없음", "실제 신호 분석은 권리 보유 업로드 음원만 사용", "저작권 안전 원칙 유지"],
    ]


def _value_update(sheet: str, cell_range: str, rows: list[list[Any]]) -> list[dict[str, Any]]:
    return [{"range": f"'{sheet}'!{cell_range}", "majorDimension": "ROWS", "values": rows}]


def _normalize(value: Any) -> str:
    text = str(value or "").casefold()
    text = re.sub(r"\[[^\]]*(remaster|official|music video|lyric|lyrics|live|cover|mv|4k|hd|ver\.?|version)[^\]]*\]", " ", text)
    text = re.sub(r"\([^\)]*(remaster|official|music video|lyric|lyrics|live|cover|mv|4k|hd|ver\.?|version)[^\)]*\)", " ", text)
    return re.sub(r"[^0-9a-z가-힣]+", "", text)


def _normalize_header(value: Any) -> str:
    return re.sub(r"[^0-9a-z]+", "", str(value or "").casefold())


def _normalize_artist(value: Any) -> str:
    text = str(value or "").casefold()
    text = re.sub(r"\b(feat\.?|ft\.?|with)\b.*$", " ", text)
    return re.sub(r"[^0-9a-z가-힣]+", "", text)


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _bpm_bucket(value: Any) -> str:
    bpm = _to_float(value)
    if bpm is None:
        return "Unknown"
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


def _windows_date() -> str:
    now = datetime.now()
    return f"{now.year}.{now.month}.{now.day}"


if __name__ == "__main__":
    main()
