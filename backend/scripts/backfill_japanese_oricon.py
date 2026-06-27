from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
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


SOURCE_REPO_URL = "https://github.com/sichengchen/oricon"
SOURCE_CSV_URL = "https://raw.githubusercontent.com/sichengchen/oricon/main/public/data/oricon_singles.csv"

JP_CHAR_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
TITLE_BALLAD_HINTS = (
    "愛",
    "恋",
    "涙",
    "夢",
    "心",
    "花",
    "雨",
    "雪",
    "夜",
    "風",
    "さくら",
    "桜",
    "ありがとう",
    "ラブ",
    "love",
    "heart",
    "dream",
)
UPTEMPO_HINTS = (
    "dance",
    "ダンス",
    "rock",
    "ロック",
    "beat",
    "ビート",
    "party",
    "パーティ",
    "disco",
    "ディスコ",
)
IDOL_POP_ARTISTS = (
    "SMAP",
    "嵐",
    "AKB48",
    "モーニング娘",
    "KinKi Kids",
    "V6",
    "KAT-TUN",
    "NEWS",
    "TOKIO",
    "光GENJI",
    "少年隊",
)
ROCK_POP_ARTISTS = (
    "B'z",
    "サザンオールスターズ",
    "Mr.Children",
    "GLAY",
    "L'Arc",
    "X JAPAN",
    "THE ALFEE",
    "BOØWY",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill real Oricon weekly singles chart references into the cloud ledger.")
    parser.add_argument("--add-count", type=int, default=10000)
    parser.add_argument("--ledger-path", default=str(LEDGER_PATH))
    parser.add_argument("--source-url", default=SOURCE_CSV_URL)
    parser.add_argument("--cache-path", default="data/cache/oricon_singles.csv")
    parser.add_argument("--date", default=_date_label())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ledger_path = Path(args.ledger_path)
    ledger = _load_ledger(ledger_path)
    existing_records = ledger.get("songs", [])
    baseline_count = int(ledger.get("baseline", {}).get("count") or 0)
    current_total = baseline_count + len(existing_records)

    rows = _load_rows(args.source_url, Path(args.cache_path))
    candidates = _build_candidates(rows)
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
        "candidate_unique_rows": len(candidates),
        "new_rows": len(new_records),
        "total_after_baseline": total_after,
        "source": SOURCE_REPO_URL,
        "lyrics_policy": "lyrics are not present in this source and are never stored",
        "dry_run": args.dry_run,
    }

    if args.dry_run:
        _print_json({**summary, "sample": [f"{row['title']} - {row['artist']}" for row in new_records[:20]]})
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
    _print_json(summary)


def _load_rows(source_url: str, cache_path: Path) -> list[dict[str, str]]:
    if cache_path.exists() and cache_path.stat().st_size > 0:
        text = cache_path.read_text(encoding="utf-8-sig")
    else:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        request = Request(source_url, headers={"User-Agent": "Hit Song Lab Japanese Oricon metadata backfill"})
        with urlopen(request, timeout=120) as response:
            data = response.read()
        cache_path.write_bytes(data)
        text = data.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def _build_candidates(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    aggregated: dict[tuple[str, str], dict[str, Any]] = {}

    for item in rows:
        title = _clean(item.get("title"))
        artist = _clean(item.get("artist"))
        if not title or not artist:
            continue
        key = (_norm(title), _norm_artist(artist))
        rank = _int(item.get("rank"), 999) or 999
        chart_date = _clean(item.get("chart_date"))
        weekly_sales = _int(item.get("weekly_sales"), 0) or 0
        total_sales = _int(item.get("total_sales"), 0) or 0
        chart_year = _int(item.get("chart_year"), None)
        source_year = _int(item.get("source_year"), None)

        row = aggregated.get(key)
        if row is None:
            aggregated[key] = {
                "title": title,
                "artist": artist,
                "best_rank": rank,
                "weekly_chart_appearances": 1,
                "max_weekly_sales": weekly_sales,
                "max_total_sales": total_sales,
                "first_chart_date": chart_date,
                "last_chart_date": chart_date,
                "first_chart_year": chart_year or source_year,
                "last_chart_year": chart_year or source_year,
                "has_japanese_script": _has_japanese(title) or _has_japanese(artist),
            }
            continue

        row["best_rank"] = min(row["best_rank"], rank)
        row["weekly_chart_appearances"] += 1
        row["max_weekly_sales"] = max(row["max_weekly_sales"], weekly_sales)
        row["max_total_sales"] = max(row["max_total_sales"], total_sales)
        if chart_date:
            row["first_chart_date"] = min(row["first_chart_date"] or chart_date, chart_date)
            row["last_chart_date"] = max(row["last_chart_date"] or chart_date, chart_date)
        year = chart_year or source_year
        if year:
            row["first_chart_year"] = min(row.get("first_chart_year") or year, year)
            row["last_chart_year"] = max(row.get("last_chart_year") or year, year)

    candidates = []
    for row in aggregated.values():
        row["preference_score"] = _preference_score(row)
        candidates.append(row)

    return sorted(
        candidates,
        key=lambda row: (
            -row["preference_score"],
            _int(row.get("best_rank"), 999),
            -_int(row.get("weekly_chart_appearances"), 0),
            -_int(row.get("max_total_sales"), 0),
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
    release_year = row.get("first_chart_year") or _release_year(row.get("first_chart_date"))
    chart_line = (
        f"Oricon weekly singles best rank #{row.get('best_rank')}, "
        f"{row.get('weekly_chart_appearances')} weekly appearances, "
        f"{row.get('first_chart_date')} to {row.get('last_chart_date')}."
    )
    sales_line = _sales_line(row)

    return {
        "title": title,
        "artist": artist,
        "genre": style["genre"],
        "country": "JP",
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
        "why_hook_works": f"Oricon chart persistence confirms Japanese-market recognition. Source signal: {chart_line} {sales_line}".strip(),
        "chord_progression": None,
        "arrangement": style["arrangement"],
        "vocal": style["vocal"],
        "mixing": style["mixing"],
        "hit_factor": f"Real Japanese singles-chart reference. {chart_line} {sales_line}".strip(),
        "producer_takeaway": style["producer_takeaway"],
        "avoid_copying": "Do not copy lyric text, melody, riff, cadence, topline contour, artist delivery, sample, arrangement signature, or sound identity. Use only metadata-level market signal and generalized structure.",
        "data_confidence": "low",
        "chart_source": "Oricon Weekly Singles Chart",
        "chart_rank": row.get("best_rank"),
        "chart_url": SOURCE_REPO_URL,
        "first_chart_date": row.get("first_chart_date"),
        "last_chart_date": row.get("last_chart_date"),
        "weeks_on_chart_signal": row.get("weekly_chart_appearances"),
        "max_weekly_sales": row.get("max_weekly_sales"),
        "max_total_sales": row.get("max_total_sales"),
        "preference_score": row.get("preference_score"),
        "added_date": added_date,
        "added_at": added_at,
        "source_type": "oricon_weekly_singles_bulk_backfill",
    }


def _style_profile(row: dict[str, Any]) -> dict[str, str]:
    text = f"{row.get('title', '')} {row.get('artist', '')}"
    lowered = text.casefold()

    if any(artist.casefold() in lowered for artist in IDOL_POP_ARTISTS):
        return {
            "genre": "J-pop Idol / Group Pop",
            "lyric_theme": "group-pop optimism, youthful memory, confession, promise, or seasonal uplift; no lyrics stored",
            "speaker_situation": "direct, memorable pop speaker aimed at broad Japanese chart listeners",
            "story_flow": "intro motif > verse setup > pre-chorus lift > title-driven chorus > repeatable tag",
            "hook_type": "title phrase + group-pop melodic hook",
            "hook_location": "chorus or post-chorus title-tag area",
            "arrangement": "bright rhythm section, clear chorus lift, unison or stacked group vocals, memorable intro motif",
            "vocal": "clean lead, chorus doubles, group response, controlled adlib lift",
            "mixing": "front vocal, bright chorus, tight low-mid control, radio-forward hook balance",
            "producer_takeaway": "Keep the title cue short, let the chorus arrive cleanly, and use group-response energy without copying any chant or choreography.",
        }

    if any(artist.casefold() in lowered for artist in ROCK_POP_ARTISTS):
        return {
            "genre": "Japanese Rock / Pop Rock",
            "lyric_theme": "longing, resolve, youth, farewell, or cathartic release; no lyrics stored",
            "speaker_situation": "first-person speaker turning private emotion into a wide chorus",
            "story_flow": "guitar/piano motif > verse restraint > pre-chorus climb > broad chorus > bridge release",
            "hook_type": "anthemic melody + title cue",
            "hook_location": "chorus climax or final chorus extension",
            "arrangement": "guitar-forward band core, melodic bass movement, drum lift, final chorus widening",
            "vocal": "verse intimacy, chorus belt or open vowel, final harmony/adlib expansion",
            "mixing": "dense but vocal-forward, wide chorus guitars, controlled cymbal brightness",
            "producer_takeaway": "Use the band lift and chorus width as structure references only; write a fresh topline and fresh riff language.",
        }

    if any(hint.casefold() in lowered for hint in UPTEMPO_HINTS):
        return {
            "genre": "Japanese Dance Pop / Uptempo",
            "lyric_theme": "movement, confidence, nightlife, youthful rush, or communal release; no lyrics stored",
            "speaker_situation": "performance-forward speaker built around an immediate title phrase",
            "story_flow": "rhythmic intro > verse pocket > lift > chorus/title hook > dance or chant tag",
            "hook_type": "rhythmic title hook + groove tag",
            "hook_location": "chorus or post-chorus",
            "arrangement": "tight drum groove, bass/synth motif, bright hook layer, short retention tag",
            "vocal": "rhythmic verse, doubled chorus, response phrase or adlib accent",
            "mixing": "tight low end, dry rhythmic lead, wider chorus, crisp transient focus",
            "producer_takeaway": "Prioritize a title phrase that can survive without context, then build the groove around that phrase.",
        }

    if any(hint.casefold() in lowered for hint in TITLE_BALLAD_HINTS):
        return {
            "genre": "Japanese Ballad / Kayokyoku Pop",
            "lyric_theme": "love, farewell, memory, rain, seasons, gratitude, or regret; no lyrics stored",
            "speaker_situation": "mature speaker reflecting on a relationship or season with restrained emotion",
            "story_flow": "quiet verse scene > emotional pre-chorus > title-centered chorus > bridge turn > expanded final chorus",
            "hook_type": "lyric statement + vocal melody hook",
            "hook_location": "chorus or bridge-to-final-chorus lift",
            "arrangement": "piano/acoustic guitar, strings or pad, restrained rhythm, final chorus harmony widening",
            "vocal": "close verse vocal, sustained chorus notes, careful vibrato, tasteful final adlib",
            "mixing": "front vocal, warm reverb, uncluttered low end, smooth high-mid presence",
            "producer_takeaway": "Let one image carry the emotion; avoid overexplaining and make the title land on a stable chord tone.",
        }

    return {
        "genre": "Japanese Chart Pop Reference",
        "lyric_theme": "Japanese singles-chart pop signal; title/artist metadata only, no lyrics stored",
        "speaker_situation": "broad-market chart speaker; verify manually before using for a specific song concept",
        "story_flow": "verse premise > lift/contrast > title hook > final payoff, inferred from pop single convention",
        "hook_type": "title phrase + Japanese chart-pop hook",
        "hook_location": "chorus or title-tag area",
        "arrangement": "needs production verification; use only as Japanese chart reference until manually inspected",
        "vocal": "needs vocal verification; do not imitate artist tone, cadence, or adlibs",
        "mixing": "needs mix verification; chart metadata does not measure loudness, depth, or stereo image",
        "producer_takeaway": "Use Oricon rank and persistence as market signal only; create a new title, melody, rhythm, and sound palette.",
    }


def _preference_score(row: dict[str, Any]) -> int:
    score = 0
    if row.get("has_japanese_script"):
        score += 90
    rank = _int(row.get("best_rank"), 999) or 999
    appearances = _int(row.get("weekly_chart_appearances"), 0) or 0
    total_sales = _int(row.get("max_total_sales"), 0) or 0
    weekly_sales = _int(row.get("max_weekly_sales"), 0) or 0
    if rank <= 1:
        score += 120
    elif rank <= 5:
        score += 92
    elif rank <= 10:
        score += 70
    elif rank <= 30:
        score += 42
    score += min(90, appearances * 3)
    score += min(45, total_sales // 10)
    score += min(20, weekly_sales // 10)
    text = f"{row.get('title', '')} {row.get('artist', '')}".casefold()
    if any(hint.casefold() in text for hint in TITLE_BALLAD_HINTS):
        score += 18
    if any(artist.casefold() in text for artist in IDOL_POP_ARTISTS + ROCK_POP_ARTISTS):
        score += 15
    return score


def _sales_line(row: dict[str, Any]) -> str:
    parts = []
    if row.get("max_weekly_sales"):
        parts.append(f"max weekly sales signal {row['max_weekly_sales']}")
    if row.get("max_total_sales"):
        parts.append(f"max total sales signal {row['max_total_sales']}")
    return "; ".join(parts)


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _norm(value: Any) -> str:
    return re.sub(r"[^0-9a-z가-힣ぁ-ゟ゠-ヿ㐀-䶿一-鿿]+", "", str(value or "").casefold())


def _norm_artist(value: Any) -> str:
    text = re.sub(r"\b(feat\.?|ft\.?|with)\b.*$", "", str(value or "").casefold())
    return re.sub(r"[^0-9a-z가-힣ぁ-ゟ゠-ヿ㐀-䶿一-鿿]+", "", text)


def _has_japanese(value: Any) -> bool:
    return bool(JP_CHAR_RE.search(str(value or "")))


def _int(value: Any, fallback: int | None) -> int | None:
    try:
        if value in (None, ""):
            return fallback
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return fallback


def _release_year(value: Any) -> int | None:
    text = str(value or "")
    match = re.search(r"(19|20)\d{2}", text)
    return int(match.group(0)) if match else None


def _date_label() -> str:
    now = datetime.now()
    return f"{now.year}.{now.month}.{now.day}"


def _print_json(payload: dict[str, Any]) -> None:
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
