from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from cloud_hit_song_batch import (
    LEDGER_PATH,
    _identity_hash,
    _load_ledger,
    _record_key,
    _record_keys,
    _save_cloud_exports,
    _save_ledger,
)


SOURCE_REPO_URL = "https://github.com/EX3exp/Kpop-lyric-datasets"
SOURCE_ZIP_URL = "https://codeload.github.com/EX3exp/Kpop-lyric-datasets/zip/refs/heads/main"

LYRICAL_GENRE_HINTS = ("발라드", "R&B", "Soul", "인디", "포크", "블루스", "OST")
UPTEMPO_GENRE_HINTS = ("댄스", "랩", "힙합", "록", "메탈", "일렉트로니카")
LYRICAL_TITLE_HINTS = (
    "사랑",
    "이별",
    "그대",
    "너",
    "나",
    "밤",
    "비",
    "눈물",
    "기억",
    "추억",
    "안녕",
    "그리움",
    "봄",
    "겨울",
    "하루",
    "마음",
    "혼자",
    "보고",
    "미안",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill Korean Melon monthly-chart song metadata into the cloud ledger.")
    parser.add_argument("--add-count", type=int, default=10000)
    parser.add_argument("--ledger-path", default=str(LEDGER_PATH))
    parser.add_argument("--source-zip-url", default=SOURCE_ZIP_URL)
    parser.add_argument("--cache-path", default="data/cache/kpop_lyric_datasets_main.zip")
    parser.add_argument("--date", default=_date_label())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ledger_path = Path(args.ledger_path)
    ledger = _load_ledger(ledger_path)
    existing_records = ledger.get("songs", [])
    baseline_count = int(ledger.get("baseline", {}).get("count") or 0)
    current_total = baseline_count + len(existing_records)

    archive_path = _ensure_archive(args.source_zip_url, Path(args.cache_path))
    candidates = _build_candidates(archive_path)
    existing_keys = _record_keys(existing_records)
    existing_hashes = set(ledger.get("baseline", {}).get("identity_hashes", []))
    existing_hashes |= {_identity_hash(row.get("title"), row.get("artist")) for row in existing_records}
    selected = _select_candidates(candidates, existing_keys, existing_hashes, args.add_count)

    now_iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    new_records = [_ledger_song(candidate, args.date, now_iso) for candidate in selected]
    updated_records = existing_records + new_records
    total_after = baseline_count + len(updated_records)
    summary = {
        "requested_add_count": args.add_count,
        "current_total_before": current_total,
        "new_rows": len(new_records),
        "total_after_baseline": total_after,
        "source": SOURCE_REPO_URL,
        "lyrics_policy": "lyrics field is ignored and never stored",
        "dry_run": args.dry_run,
    }

    if args.dry_run:
        print(json.dumps({**summary, "sample": [f"{row['title']} - {row['artist']}" for row in new_records[:20]]}, ensure_ascii=False, indent=2))
        return

    updated_ledger = {
        **ledger,
        "version": 1,
        "updated_at": now_iso,
        "total_after_baseline": total_after,
        "songs": updated_records,
    }
    _save_ledger(ledger_path, updated_ledger)
    _save_cloud_exports(updated_ledger)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _ensure_archive(source_url: str, cache_path: Path) -> Path:
    if cache_path.exists() and cache_path.stat().st_size > 0:
        return cache_path
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(source_url, headers={"User-Agent": "Hit Song Lab Korean metadata backfill"})
    with urlopen(request, timeout=180) as response:
        cache_path.write_bytes(response.read())
    return cache_path


def _build_candidates(archive_path: Path) -> list[dict[str, Any]]:
    aggregated: dict[tuple[str, str], dict[str, Any]] = {}
    chart_counts: defaultdict[tuple[str, str], int] = defaultdict(int)

    with zipfile.ZipFile(archive_path) as archive:
        names = [
            name
            for name in archive.namelist()
            if "/melon/monthly-chart/" in name and name.endswith(".json")
        ]
        for name in names:
            with archive.open(name) as file:
                item = json.loads(file.read().decode("utf-8"))
            song_name = _clean(item.get("song_name"))
            artist = _clean(item.get("artist"))
            if not song_name or not artist:
                continue

            info = _info(item)
            year = _int(info.get("year"), None)
            month = _int(info.get("month"), None)
            rank = _int(info.get("rank"), 999)
            chart_date = _chart_date(year, month)
            key = (_norm(song_name), _norm_artist(artist))
            chart_counts[key] += 1

            row = aggregated.get(key)
            if row is None:
                aggregated[key] = {
                    "title": song_name,
                    "artist": artist,
                    "genre_raw": _clean(item.get("genre")),
                    "album": _clean(item.get("album")),
                    "release_date": _clean(item.get("release_date")),
                    "lyric_writer": _clean(item.get("lyric_writer")),
                    "composer": _clean(item.get("composer")),
                    "arranger": _clean(item.get("arranger")),
                    "melon_song_id": _clean(item.get("song_id")),
                    "first_chart_date": chart_date,
                    "last_chart_date": chart_date,
                    "best_rank": rank,
                    "monthly_chart_appearances": 1,
                }
                continue

            row["genre_raw"] = row["genre_raw"] or _clean(item.get("genre"))
            row["album"] = row["album"] or _clean(item.get("album"))
            row["release_date"] = row["release_date"] or _clean(item.get("release_date"))
            row["lyric_writer"] = row["lyric_writer"] or _clean(item.get("lyric_writer"))
            row["composer"] = row["composer"] or _clean(item.get("composer"))
            row["arranger"] = row["arranger"] or _clean(item.get("arranger"))
            row["melon_song_id"] = row["melon_song_id"] or _clean(item.get("song_id"))
            row["first_chart_date"] = min(row["first_chart_date"], chart_date)
            row["last_chart_date"] = max(row["last_chart_date"], chart_date)
            row["best_rank"] = min(row["best_rank"], rank)
            row["monthly_chart_appearances"] = chart_counts[key]

    rows = []
    for row in aggregated.values():
        row["preference_score"] = _preference_score(row)
        rows.append(row)

    return sorted(
        rows,
        key=lambda row: (
            -row["preference_score"],
            _int(row.get("best_rank"), 999),
            -_int(row.get("monthly_chart_appearances"), 0),
            row.get("first_chart_date") or "",
            row["title"],
        ),
    )


def _select_candidates(
    candidates: list[dict[str, Any]],
    existing_keys: set[tuple[str, str]],
    existing_hashes: set[str],
    add_count: int,
) -> list[dict[str, Any]]:
    if add_count <= 0:
        return []
    selected = []
    selected_keys = set()
    for row in candidates:
        key = _record_key(row)
        identity_hash = _identity_hash(row.get("title"), row.get("artist"))
        if key in existing_keys or key in selected_keys or identity_hash in existing_hashes:
            continue
        selected.append(row)
        selected_keys.add(key)
        if len(selected) >= add_count:
            break
    return selected


def _ledger_song(row: dict[str, Any], added_date: str, added_at: str) -> dict[str, Any]:
    style = _style_profile(row)
    title = row["title"]
    artist = row["artist"]
    release_year = _release_year(row.get("release_date")) or _release_year(row.get("first_chart_date"))
    chart_line = (
        f"Melon monthly chart best rank #{row.get('best_rank')}, "
        f"{row.get('monthly_chart_appearances')} monthly appearances, "
        f"{row.get('first_chart_date')} to {row.get('last_chart_date')}."
    )
    credits = _credits(row)

    return {
        "title": title,
        "artist": artist,
        "genre": style["genre"],
        "country": "KR",
        "release_year": release_year,
        "bpm": None,
        "key": None,
        "youtube_url": "https://www.youtube.com/results?search_query=" + quote_plus(f"{artist} {title} official"),
        "lyric_theme": style["lyric_theme"],
        "speaker_situation": style["speaker_situation"],
        "story_flow": style["story_flow"],
        "hook_type": style["hook_type"],
        "hook_location": style["hook_location"],
        "hook_cue": f"title cue: {title}",
        "hook_melody_interval": "low-confidence; not transcribed from audio",
        "hook_melody_rhythm": "low-confidence; not transcribed from audio",
        "why_hook_works": f"Melon monthly-chart repetition confirms Korean listener recognition. Source signal: {chart_line}",
        "chord_progression": None,
        "arrangement": style["arrangement"],
        "vocal": style["vocal"],
        "mixing": style["mixing"],
        "hit_factor": f"Real Korean chart metadata reference. {chart_line}",
        "producer_takeaway": style["producer_takeaway"],
        "avoid_copying": "Do not copy lyric text, melody, riff, cadence, topline contour, artist delivery, sample, or sound signature. Use only metadata-level market signal and generalized structure.",
        "data_confidence": "low",
        "chart_source": "Melon Monthly Chart Top 100",
        "chart_rank": row.get("best_rank"),
        "chart_url": SOURCE_REPO_URL,
        "first_chart_date": row.get("first_chart_date"),
        "last_chart_date": row.get("last_chart_date"),
        "weeks_on_chart_signal": row.get("monthly_chart_appearances"),
        "melon_song_id": row.get("melon_song_id"),
        "album": row.get("album"),
        "credits": credits,
        "source_genre": row.get("genre_raw"),
        "preference_score": row.get("preference_score"),
        "added_date": added_date,
        "added_at": added_at,
        "source_type": "melon_monthly_chart_bulk_backfill",
    }


def _style_profile(row: dict[str, Any]) -> dict[str, str]:
    genre = row.get("genre_raw") or ""
    title = row.get("title") or ""

    if "발라드" in genre or "OST" in genre:
        return {
            "genre": "Korean Ballad / OST",
            "lyric_theme": "이별, 그리움, 고백, 회상, 후회, 위로 같은 한국형 서정 정서; 가사 전문은 저장하지 않음",
            "speaker_situation": "관계의 끝이나 남은 마음을 조용히 돌아보는 1인칭 화자",
            "story_flow": "낮은 밀도의 벌스 > 감정 압력을 올리는 프리코러스 > 제목 중심 코러스 > 브리지 시점 전환 > 마지막 코러스 확장",
            "hook_type": "lyric statement + vocal melody hook",
            "hook_location": "chorus or bridge climax, inferred from Korean ballad convention",
            "arrangement": "piano, acoustic guitar, strings, pad, restrained drums, final chorus vocal widening",
            "vocal": "close verse vocal, sustained chorus notes, controlled vibrato, final adlib or harmony lift",
            "mixing": "front vocal, warm reverb, controlled low end, uncluttered high-mid presence",
            "producer_takeaway": "첫 벌스는 얇게 두고, 코러스 첫 문장을 제목 감정으로 명확히 세운 뒤 마지막 코러스에서 화성/보컬을 확장하세요.",
        }

    if any(hint in genre for hint in ("R&B", "Soul", "인디", "포크", "블루스")):
        return {
            "genre": "Korean Lyrical Pop / R&B",
            "lyric_theme": "일상 장면, 밤, 거리, 기억, 관계의 온도 같은 서정적 소재; 가사 전문은 저장하지 않음",
            "speaker_situation": "작은 장면을 통해 큰 감정을 우회적으로 말하는 화자",
            "story_flow": "groove or guitar/piano motif > intimate verse > melodic chorus > bridge color change > restrained final hook",
            "hook_type": "melodic phrase + title cue hook",
            "hook_location": "chorus or repeated title-tag area",
            "arrangement": "warm keys, guitar, light rhythm section, chorus harmony doubles, space-aware adlibs",
            "vocal": "soft rhythmic verse, open chorus vowel, tasteful harmony or response vocal",
            "mixing": "vocal close, room or plate reverb, soft transient control, warm low-mid body",
            "producer_takeaway": "화려한 사운드보다 반복 가능한 짧은 제목 큐와 보컬 질감을 먼저 설계하세요.",
        }

    if "댄스" in genre:
        return {
            "genre": "K-pop Dance",
            "lyric_theme": "매력, 선언, 설렘, 자신감, 관계의 긴장감을 짧은 제목 큐로 압축; 가사 전문은 저장하지 않음",
            "speaker_situation": "리듬 위에서 직접적으로 감정이나 태도를 던지는 퍼포먼스형 화자",
            "story_flow": "intro motif > verse groove > pre-chorus lift > chorus title hook > post-hook dance tag",
            "hook_type": "title phrase + groove/performance hook",
            "hook_location": "chorus, post-chorus, or point choreography area",
            "arrangement": "drum groove, bass/synth motif, pre-chorus lift, post-chorus retention device",
            "vocal": "rhythmic lead, stacked hook doubles, group response or adlib accent",
            "mixing": "tight low end, bright hook lead, wide chorus, dry rhythmic vocal focus",
            "producer_takeaway": "포인트 안무가 없어도 기억되는 리듬 훅을 만들고, 제목 큐는 짧게 반복하세요.",
        }

    if any(hint in genre for hint in ("랩", "힙합")):
        return {
            "genre": "Korean Hip-Hop / Rap Pop",
            "lyric_theme": "자기 선언, 관계 긴장, 도시적 태도, 리듬 중심 캐치프레이즈; 가사 전문은 저장하지 않음",
            "speaker_situation": "비트 포켓 안에서 태도와 이미지를 빠르게 제시하는 화자",
            "story_flow": "beat identity > rap verse > title phrase hook > second verse escalation > final hook",
            "hook_type": "rhythmic phrase + beat-pocket hook",
            "hook_location": "hook phrase or post-hook tag",
            "arrangement": "drum/bass pocket, sparse motif, negative space, hook word accent",
            "vocal": "tight rhythm, doubles on catchphrase, selective adlibs",
            "mixing": "dry vocal center, defined bass, narrow verse/wider hook contrast",
            "producer_takeaway": "새로운 리듬 캐치프레이즈와 비트 포켓만 참고하고, 원곡 플로우나 라인은 절대 따라가지 마세요.",
        }

    return {
        "genre": "Korean Pop Reference",
        "lyric_theme": "한국 차트권 팝 감정, 관계, 계절, 일상 이미지; 메타데이터 기반 추정",
        "speaker_situation": "짧은 제목 기억 장치를 중심으로 감정을 정리하는 한국어 팝 화자",
        "story_flow": "verse premise > lift or contrast > title hook > final payoff",
        "hook_type": "title phrase + Korean pop hook",
        "hook_location": "chorus or title-tag area",
        "arrangement": "needs production verification; use only as Korean chart reference until manually inspected",
        "vocal": "needs vocal verification; do not imitate artist tone, cadence, or adlibs",
        "mixing": "needs mix verification; chart metadata does not measure loudness, depth, or stereo image",
        "producer_takeaway": "차트 신호와 제목/장르만 참고하고, 멜로디·가사·사운드는 새로 설계하세요.",
    }


def _preference_score(row: dict[str, Any]) -> int:
    genre = row.get("genre_raw") or ""
    title = row.get("title") or ""
    score = 0
    if any(hint in genre for hint in LYRICAL_GENRE_HINTS):
        score += 60
    if any(hint in title for hint in LYRICAL_TITLE_HINTS):
        score += 18
    if not any(hint in genre for hint in UPTEMPO_GENRE_HINTS):
        score += 10
    rank = _int(row.get("best_rank"), 999)
    appearances = _int(row.get("monthly_chart_appearances"), 0)
    if rank <= 1:
        score += 25
    elif rank <= 10:
        score += 18
    elif rank <= 40:
        score += 10
    score += min(25, appearances)
    return score


def _info(item: dict[str, Any]) -> dict[str, Any]:
    info = item.get("info")
    if isinstance(info, list) and info and isinstance(info[0], dict):
        return info[0]
    return {}


def _credits(row: dict[str, Any]) -> str:
    parts = []
    if row.get("lyric_writer"):
        parts.append(f"lyric: {row['lyric_writer']}")
    if row.get("composer"):
        parts.append(f"composer: {row['composer']}")
    if row.get("arranger"):
        parts.append(f"arranger: {row['arranger']}")
    return " / ".join(parts)


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _norm(value: Any) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", str(value or "").casefold())


def _norm_artist(value: Any) -> str:
    text = re.sub(r"\b(feat\.?|ft\.?|with)\b.*$", "", str(value or "").casefold())
    return re.sub(r"[^0-9a-z가-힣]+", "", text)


def _int(value: Any, fallback: int | None) -> int | None:
    try:
        if value in (None, ""):
            return fallback
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _release_year(value: Any) -> int | None:
    text = str(value or "")
    match = re.search(r"(19|20)\d{2}", text)
    return int(match.group(0)) if match else None


def _chart_date(year: int | None, month: int | None) -> str:
    if not year or not month:
        return "0000-00"
    return f"{year:04d}-{month:02d}"


def _date_label() -> str:
    now = datetime.now()
    return f"{now.year}.{now.month}.{now.day}"


if __name__ == "__main__":
    main()
