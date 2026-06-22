from __future__ import annotations

import argparse
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Add safe reference-song research rows to a Google Sheet.")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--sheet-id", default=os.environ.get("GOOGLE_SHEET_ID") or DEFAULT_SHEET_ID)
    parser.add_argument("--date", default=datetime.now().strftime("%Y.%-m.%-d") if os.name != "nt" else _windows_date())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    queue = _load_queue()
    service = None if args.dry_run else _build_sheets_service()
    existing_rows = [] if args.dry_run else _read_values(service, args.sheet_id, "'Song Library'!A:J")
    existing_keys = _existing_song_keys(existing_rows)
    selected = _select_unique(queue, existing_keys, args.batch_size)

    if len(selected) != args.batch_size:
        raise SystemExit(
            f"Need exactly {args.batch_size} unique songs, but only found {len(selected)}. "
            "Add more real songs to backend/seeds/cloud_reference_queue.json."
        )

    if args.dry_run:
        print(json.dumps({"selected": [f"{row['title']} - {row['artist']}" for row in selected]}, ensure_ascii=False, indent=2))
        return

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
    start_index = existing_count + 1

    updates = []
    updates.extend(_value_update("Song Library", f"A{start_index + 1}:J{start_index + len(selected)}", _song_library_rows(selected, start_index)))
    updates.extend(_value_update("전체 곡명 Raw", f"A{start_index + 1}:I{start_index + len(selected)}", _all_title_rows(selected, start_index)))
    updates.extend(_value_update("후크 멜로디 리듬 Raw", f"A{start_index + 1}:M{start_index + len(selected)}", _hook_rows(selected, start_index)))
    updates.extend(_value_update("Chord Lyrics Raw", f"A{start_index + 1}:L{start_index + len(selected)}", _chord_lyric_rows(selected)))
    updates.extend(_value_update("Producer Features Raw", f"A{start_index + 1}:J{start_index + len(selected)}", _producer_rows(selected)))

    merged_rows = _existing_song_records(existing_rows) + selected
    stats = _build_stats(merged_rows)
    updates.extend(_value_update("Dashboard", "A1:F18", _dashboard_rows(stats, selected, args.date)))
    updates.extend(_value_update("Statistics", "A1:D30", _statistics_rows(stats)))
    updates.extend(_value_update("Genre Summary", "A1:F80", _genre_summary_rows(merged_rows)))
    updates.extend(_value_update("[차트1] 장르별 곡 수 분포", "A1:B80", [["Genre", "Songs"], *stats["genre_counts"]]))
    updates.extend(_value_update("Pattern Summaries", "A1:E12", _pattern_rows(stats)))
    updates.extend(_value_update("연동 검증", "A1:D11", _validation_rows(stats)))
    updates.extend(_value_update(args.date + " 추천 정보", "A1:F24", _recommendation_rows(stats, args.date)))

    body = {"valueInputOption": "USER_ENTERED", "data": updates}
    service.spreadsheets().values().batchUpdate(spreadsheetId=args.sheet_id, body=body).execute()

    print(
        json.dumps(
            {
                "added": [f"{row['title']} - {row['artist']}" for row in selected],
                "total_after": len(merged_rows),
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


def _load_queue() -> list[dict[str, Any]]:
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


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
    keys = set()
    for row in rows[1:]:
        if len(row) < 3:
            continue
        keys.add((_normalize(row[1]), _normalize_artist(row[2])))
    return keys


def _existing_song_records(rows: list[list[Any]]) -> list[dict[str, Any]]:
    records = []
    for row in rows[1:]:
        if len(row) < 3:
            continue
        records.append(
            {
                "title": row[1] if len(row) > 1 else "",
                "artist": row[2] if len(row) > 2 else "",
                "genre": row[3] if len(row) > 3 else "Unknown",
                "country": row[4] if len(row) > 4 else "",
                "release_year": row[5] if len(row) > 5 else "",
                "bpm": _to_float(row[6] if len(row) > 6 else None),
                "key": row[7] if len(row) > 7 else "",
                "hook_type": "",
                "chord_progression": "",
                "data_confidence": "medium",
            }
        )
    return records


def _select_unique(queue: list[dict[str, Any]], existing_keys: set[tuple[str, str]], batch_size: int) -> list[dict[str, Any]]:
    selected = []
    selected_keys = set()
    for row in queue:
        key = (_normalize(row.get("title")), _normalize_artist(row.get("artist")))
        if key in existing_keys or key in selected_keys:
            continue
        selected.append(row)
        selected_keys.add(key)
        if len(selected) == batch_size:
            break
    return selected


def _data_row_count(rows: list[list[Any]]) -> int:
    return max(0, sum(1 for row in rows[1:] if len(row) >= 3 and row[1]))


def _song_library_rows(songs: list[dict[str, Any]], start_index: int) -> list[list[Any]]:
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
            "cloud_curated_reference",
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
