from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
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


BILLBOARD_ALL_JSON_URL = "https://raw.githubusercontent.com/mhollingshead/billboard-hot-100/main/all.json"

LYRICAL_POP_ARTISTS = {
    "adele",
    "alicia keys",
    "amy winehouse",
    "barbra streisand",
    "beyonce",
    "billie eilish",
    "bruno mars",
    "celine dion",
    "christina aguilera",
    "coldplay",
    "ed sheeran",
    "ellie goulding",
    "george michael",
    "harry styles",
    "james arthur",
    "james blunt",
    "john legend",
    "justin bieber",
    "katy perry",
    "kelly clarkson",
    "lady gaga",
    "lana del rey",
    "leona lewis",
    "lewis capaldi",
    "lorde",
    "mariah carey",
    "miley cyrus",
    "olivia rodrigo",
    "pink",
    "rihanna",
    "robyn",
    "sabrina carpenter",
    "sam smith",
    "sara bareilles",
    "sia",
    "taylor swift",
    "the weeknd",
    "whitney houston",
}

BALLAD_TITLE_WORDS = {
    "again",
    "alone",
    "always",
    "beautiful",
    "believe",
    "blue",
    "broken",
    "cry",
    "dream",
    "fall",
    "forever",
    "goodbye",
    "heart",
    "heaven",
    "home",
    "hurt",
    "i love",
    "lonely",
    "love",
    "memory",
    "miss",
    "need",
    "night",
    "rain",
    "remember",
    "sad",
    "save",
    "say",
    "someone",
    "sorry",
    "stay",
    "tears",
    "tonight",
    "wait",
    "when",
    "without",
    "you",
}

UPTEMPO_WORDS = {
    "dance",
    "party",
    "funk",
    "shake",
    "rock",
    "hot",
    "club",
    "fire",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill real Billboard Hot 100 reference songs into the cloud ledger.")
    parser.add_argument("--target-total", type=int, default=10000, help="Target total_after_baseline count.")
    parser.add_argument("--max-add", type=int, default=None, help="Maximum new rows to add this run.")
    parser.add_argument("--ledger-path", default=str(LEDGER_PATH))
    parser.add_argument("--source-url", default=BILLBOARD_ALL_JSON_URL)
    parser.add_argument("--cache-path", default="data/cache/billboard_hot100_all.json")
    parser.add_argument("--date", default=_date_label())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ledger_path = Path(args.ledger_path)
    ledger = _load_ledger(ledger_path)
    existing_records = ledger.get("songs", [])
    baseline_count = int(ledger.get("baseline", {}).get("count") or 0)
    current_total = baseline_count + len(existing_records)
    needed = max(0, args.target_total - current_total)
    if args.max_add is not None:
        needed = min(needed, args.max_add)

    charts = _load_charts(args.source_url, Path(args.cache_path))
    candidates = _build_candidates(charts)
    existing_keys = _record_keys(existing_records)
    existing_hashes = set(ledger.get("baseline", {}).get("identity_hashes", []))
    existing_hashes |= {_identity_hash(row.get("title"), row.get("artist")) for row in existing_records}
    selected = _select_candidates(candidates, existing_keys, existing_hashes, needed)

    now_iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    new_records = [_ledger_song(candidate, args.date, now_iso) for candidate in selected]
    updated_records = existing_records + new_records
    total_after = baseline_count + len(updated_records)

    summary = {
        "requested_target_total": args.target_total,
        "current_total_before": current_total,
        "new_rows": len(new_records),
        "total_after_baseline": total_after,
        "preferred_pop_ballad_first": True,
        "source": args.source_url,
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


def _load_charts(source_url: str, cache_path: Path) -> list[dict[str, Any]]:
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(source_url, headers={"User-Agent": "Hit Song Lab research backfill"})
    with urlopen(request, timeout=120) as response:
        body = response.read().decode("utf-8")
    cache_path.write_text(body, encoding="utf-8")
    return json.loads(body)


def _build_candidates(charts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregated: dict[tuple[str, str], dict[str, Any]] = {}
    chart_counts: defaultdict[tuple[str, str], int] = defaultdict(int)

    for chart in charts:
        date = chart.get("date")
        for item in chart.get("data", []):
            title = _clean_text(item.get("song"))
            artist = _clean_text(item.get("artist"))
            if not title or not artist:
                continue
            key = (_norm(title), _norm_artist(artist))
            rank = _int(item.get("this_week"), 101)
            peak = _int(item.get("peak_position"), rank)
            weeks = _int(item.get("weeks_on_chart"), 0)
            chart_counts[key] += 1

            row = aggregated.get(key)
            if row is None:
                aggregated[key] = {
                    "title": title,
                    "artist": artist,
                    "first_chart_date": date,
                    "last_chart_date": date,
                    "best_rank": rank,
                    "peak_position": peak,
                    "max_weeks_on_chart": weeks,
                    "chart_appearances": 1,
                }
                continue

            row["first_chart_date"] = min(row["first_chart_date"], date)
            row["last_chart_date"] = max(row["last_chart_date"], date)
            row["best_rank"] = min(row["best_rank"], rank)
            row["peak_position"] = min(row["peak_position"], peak)
            row["max_weeks_on_chart"] = max(row["max_weeks_on_chart"], weeks)
            row["chart_appearances"] = chart_counts[key]

    rows = []
    for row in aggregated.values():
        row["preference_score"] = _preference_score(row)
        rows.append(row)

    return sorted(
        rows,
        key=lambda row: (
            -row["preference_score"],
            _int(row.get("peak_position"), 101),
            -_int(row.get("max_weeks_on_chart"), 0),
            row.get("first_chart_date") or "",
            row["title"].casefold(),
        ),
    )


def _select_candidates(
    candidates: list[dict[str, Any]],
    existing_keys: set[tuple[str, str]],
    existing_hashes: set[str],
    needed: int,
) -> list[dict[str, Any]]:
    if needed <= 0:
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
        if len(selected) >= needed:
            break
    return selected


def _ledger_song(row: dict[str, Any], added_date: str, added_at: str) -> dict[str, Any]:
    style = _style_profile(row)
    title = row["title"]
    artist = row["artist"]
    first_year = _year(row.get("first_chart_date"))
    youtube_query = f"{artist} {title} official"
    chart_line = (
        f"Billboard Hot 100 peak #{row.get('peak_position')}, "
        f"{row.get('max_weeks_on_chart')} max weeks-on-chart signal, first charted {row.get('first_chart_date')}."
    )

    return {
        "title": title,
        "artist": artist,
        "genre": style["genre"],
        "country": "US/Global",
        "release_year": first_year,
        "bpm": None,
        "key": None,
        "youtube_url": "https://www.youtube.com/results?search_query=" + _quote_plus(youtube_query),
        "lyric_theme": style["lyric_theme"],
        "speaker_situation": style["speaker_situation"],
        "story_flow": style["story_flow"],
        "hook_type": style["hook_type"],
        "hook_location": style["hook_location"],
        "hook_cue": f"title cue: {title}",
        "hook_melody_interval": "low-confidence; not transcribed from audio",
        "hook_melody_rhythm": "low-confidence; not transcribed from audio",
        "why_hook_works": f"The title is a real chart-recognized identity handle. Source signal: {chart_line}",
        "chord_progression": None,
        "arrangement": style["arrangement"],
        "vocal": style["vocal"],
        "mixing": style["mixing"],
        "hit_factor": f"Real Billboard Hot 100 chart entry. {chart_line}",
        "producer_takeaway": style["producer_takeaway"],
        "avoid_copying": "Do not copy lyric text, melody, riff, cadence, topline contour, artist delivery, sample, or sound signature. Use only title-level market signal and generalized structure.",
        "data_confidence": "low",
        "chart_source": "Billboard Hot 100 archive",
        "chart_rank": row.get("peak_position"),
        "chart_url": BILLBOARD_ALL_JSON_URL,
        "first_chart_date": row.get("first_chart_date"),
        "last_chart_date": row.get("last_chart_date"),
        "weeks_on_chart_signal": row.get("max_weeks_on_chart"),
        "preference_score": row.get("preference_score"),
        "added_date": added_date,
        "added_at": added_at,
        "source_type": "billboard_hot100_bulk_backfill",
    }


def _style_profile(row: dict[str, Any]) -> dict[str, str]:
    title = row["title"].casefold()
    artist = _artist_base(row["artist"])
    score = row.get("preference_score", 0)
    is_ballad = score >= 40 and not any(word in title for word in UPTEMPO_WORDS)
    is_known_pop = any(name in artist for name in LYRICAL_POP_ARTISTS)

    if is_ballad:
        return {
            "genre": "Pop Ballad / Soft Pop",
            "lyric_theme": "longing, memory, love, regret, healing, or self-recognition inferred from title and chart context",
            "speaker_situation": "intimate narrator addressing a relationship, absence, recovery, or a private emotional turning point",
            "story_flow": "quiet verse premise > emotional pressure build > chorus title statement > bridge perspective shift > final chorus lift",
            "hook_type": "lyric statement + vocal melody hook",
            "hook_location": "chorus or bridge climax, inferred from pop-ballad convention",
            "arrangement": "piano, guitar, pad, or sparse groove foundation with gradual chorus widening; verify before detailed use",
            "vocal": "close verse vocal, open chorus phrasing, restrained doubles, final lift or harmony support",
            "mixing": "front vocal, warm space, controlled low end, uncluttered final chorus width",
            "producer_takeaway": "Start with restraint, place one clear emotional sentence in the chorus, and save the widest arrangement layer for the final chorus.",
        }

    if is_known_pop:
        return {
            "genre": "Lyrical Pop",
            "lyric_theme": "direct pop emotion, romance, identity, nostalgia, or confidence centered on a memorable title cue",
            "speaker_situation": "first-person or direct-address speaker compressing a relatable feeling into a short hook phrase",
            "story_flow": "verse situation > pre-chorus lift > chorus title cue > second verse detail > bridge or final chorus expansion",
            "hook_type": "title phrase + melodic/rhythmic hook",
            "hook_location": "chorus or post-chorus title area, inferred from chart-pop convention",
            "arrangement": "clear loop or chord bed, restrained verse, stronger chorus layering, memorable post-hook or tag",
            "vocal": "clean lead, chorus doubles, selective harmony or adlib lift",
            "mixing": "centered vocal, bright hook elements, streaming-friendly chorus width",
            "producer_takeaway": "Use the chart placement as market signal, then write a new title phrase, melody, and emotional angle from scratch.",
        }

    return {
        "genre": "Hot 100 Pop Reference",
        "lyric_theme": "chart-visible title, identity, relationship, place, attitude, or story cue; metadata-only inference",
        "speaker_situation": "a chart-pop speaker or narrator organized around a short title memory handle",
        "story_flow": "modern hit framework: verse premise > lift or contrast > title hook > repeatable final payoff",
        "hook_type": "title phrase + chart hook",
        "hook_location": "chorus, post-chorus, or title-tag area, inferred from chart convention",
        "arrangement": "needs production verification; use only as chart reference until inspected manually",
        "vocal": "needs vocal verification; do not imitate artist-specific tone, cadence, or adlibs",
        "mixing": "needs mix verification; chart metadata does not measure loudness, depth, or stereo image",
        "producer_takeaway": "Treat this as a market map entry: keep the hit signal, but create a new concept, melody, lyric, and sound palette.",
    }


def _preference_score(row: dict[str, Any]) -> int:
    title = row["title"].casefold()
    artist = _artist_base(row["artist"])
    score = 0
    if any(name in artist for name in LYRICAL_POP_ARTISTS):
        score += 45
    if any(word in title for word in BALLAD_TITLE_WORDS):
        score += 22
    if not any(word in title for word in UPTEMPO_WORDS):
        score += 8
    peak = _int(row.get("peak_position"), 101)
    weeks = _int(row.get("max_weeks_on_chart"), 0)
    if peak <= 1:
        score += 25
    elif peak <= 10:
        score += 18
    elif peak <= 40:
        score += 8
    score += min(20, weeks // 3)
    return score


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _norm(value: Any) -> str:
    return re.sub(r"[^0-9a-z]+", "", str(value or "").casefold())


def _norm_artist(value: Any) -> str:
    return re.sub(r"\b(feat\.?|ft\.?|with)\b.*$", "", _norm(value))


def _artist_base(value: Any) -> str:
    return re.sub(r"\b(feat\.?|ft\.?|with)\b.*$", "", str(value or "").casefold())


def _int(value: Any, fallback: int) -> int:
    try:
        if value in (None, ""):
            return fallback
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _year(value: Any) -> int | None:
    text = str(value or "")
    return int(text[:4]) if re.match(r"^\d{4}", text) else None


def _quote_plus(value: str) -> str:
    from urllib.parse import quote_plus

    return quote_plus(value)


def _date_label() -> str:
    now = datetime.now()
    return f"{now.year}.{now.month}.{now.day}"


if __name__ == "__main__":
    main()
