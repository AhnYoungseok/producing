from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH = ROOT_DIR / "backend" / "data" / "hit_song_lab.db"
QUEUE_PATH = ROOT_DIR / "backend" / "seeds" / "cloud_reference_queue.json"

CHARTS = [
    {
        "name": "Billboard Hot 100",
        "url": "https://www.billboard.com/charts/hot-100/",
        "genre": "Chart Pop",
        "country": "US",
    },
    {
        "name": "Billboard Korea Global K-Songs",
        "url": "https://www.billboard.com/charts/billboard-korea-global-k-songs/",
        "genre": "K-pop / Global Pop",
        "country": "KR",
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepend current Billboard chart songs to the reference queue.")
    parser.add_argument("--per-chart", type=int, default=25, help="Maximum rows to read from each chart.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    queue = _load_queue()
    db_keys = _load_db_keys()
    queue_keys = {_identity_key(row.get("title"), row.get("artist")) for row in queue}
    queue_keys.discard(("", ""))

    chart_rows_by_name: list[list[dict[str, Any]]] = []
    for chart in CHARTS:
        rows = _fetch_chart_rows(chart, args.per_chart)
        chart_rows_by_name.append(rows)

    captured_at = datetime.now(timezone.utc).isoformat()
    new_entries: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    selected_keys: set[tuple[str, str]] = set()

    for row in _interleave(chart_rows_by_name):
        key = _identity_key(row["title"], row["artist"])
        if key in selected_keys:
            skipped.append({**row, "reason": "duplicate_in_chart_selection"})
            continue
        if key in db_keys:
            skipped.append({**row, "reason": "already_in_local_database"})
            continue
        if key in queue_keys:
            skipped.append({**row, "reason": "already_in_reference_queue"})
            continue
        entry = _queue_entry(row, captured_at)
        new_entries.append(entry)
        selected_keys.add(key)

    result = {
        "captured_at": captured_at,
        "charts": [{"name": chart["name"], "url": chart["url"]} for chart in CHARTS],
        "new_entries": len(new_entries),
        "skipped": len(skipped),
        "preview": [f"{row['title']} - {row['artist']} ({row['chart_source']} #{row['chart_rank']})" for row in new_entries[:20]],
        "skipped_preview": [
            f"{row['title']} - {row['artist']} ({row['reason']})" for row in skipped[:20]
        ],
        "youtube_policy": "YouTube URLs are search/reference metadata only. No YouTube audio download, extraction, capture, conversion, separation, or analysis.",
    }

    if args.dry_run:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    QUEUE_PATH.write_text(json.dumps([*new_entries, *queue], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["queue_path"] = str(QUEUE_PATH)
    result["queue_total_after"] = len(new_entries) + len(queue)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _fetch_chart_rows(chart: dict[str, str], limit: int) -> list[dict[str, Any]]:
    request = urllib.request.Request(chart["url"], headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        markup = response.read().decode("utf-8", "replace")

    chunks = re.split(r'<li[^>]*a-chart-result-item-container[^>]*>', markup)[1:]
    rows: list[dict[str, Any]] = []
    for chunk in chunks:
        title_match = re.search(r'<h3[^>]*class="[^"]*c-title[^"]*"[^>]*>(.*?)</h3>', chunk, re.S)
        artist_match = re.search(r'<span[^>]*class="[^"]*c-label[^"]*"[^>]*>(.*?)</span>', chunk, re.S)
        if not title_match or not artist_match:
            continue
        title = _clean_html(title_match.group(1))
        artist = _clean_html(artist_match.group(1))
        if not title or not artist:
            continue
        rows.append(
            {
                "title": title,
                "artist": artist,
                "chart_source": chart["name"],
                "chart_url": chart["url"],
                "chart_rank": len(rows) + 1,
                "genre": chart["genre"],
                "country": chart["country"],
            }
        )
        if len(rows) >= limit:
            break
    return rows


def _queue_entry(row: dict[str, Any], captured_at: str) -> dict[str, Any]:
    title = row["title"]
    artist = row["artist"]
    theme = _infer_theme(title)
    chart_ref = f"{row['chart_source']} #{row['chart_rank']}"
    youtube_query = urllib.parse.quote_plus(f"{artist} {title} official")
    hook_cue = _short_cue(title)
    return {
        "title": title,
        "artist": artist,
        "genre": row["genre"],
        "country": row["country"],
        "release_year": None,
        "bpm": None,
        "key": None,
        "youtube_url": f"https://www.youtube.com/results?search_query={youtube_query}",
        "lyric_theme": f"{theme}; low-confidence title/chart-metadata inference only.",
        "speaker_situation": _speaker_for_theme(theme),
        "story_flow": "Likely modern hit structure: verse frames the situation, pre-chorus raises tension, chorus locks the title cue, bridge or final chorus widens the emotional color. Needs lyric verification.",
        "hook_type": "title phrase + melodic/rhythmic hook",
        "hook_location": "chorus or post-chorus title area, inferred from chart-pop convention",
        "hook_cue": hook_cue,
        "hook_melody_interval": "low-confidence; not transcribed from audio",
        "hook_melody_rhythm": "low-confidence; not transcribed from audio",
        "why_hook_works": f"The title is concise and chart-visible, giving the listener a quick memory handle; source signal: {chart_ref}.",
        "chord_progression": None,
        "arrangement": "Needs production verification; use only as current-market chart reference.",
        "vocal": "Needs vocal verification; do not imitate artist-specific tone or ad-libs.",
        "mixing": "Needs mix verification; chart metadata does not measure vocal position or loudness.",
        "hit_factor": f"Current chart placement from {chart_ref}.",
        "producer_takeaway": "Use the chart placement as market signal, then design a new title hook, groove, and concept without copying melody, lyrics, or artist signature.",
        "avoid_copying": "Do not reuse the original title concept as a template, melodic contour, lyric phrase, arrangement signature, or artist delivery.",
        "data_confidence": "low",
        "chart_source": row["chart_source"],
        "chart_rank": row["chart_rank"],
        "chart_url": row["chart_url"],
        "chart_captured_at": captured_at,
    }


def _load_queue() -> list[dict[str, Any]]:
    if not QUEUE_PATH.exists():
        return []
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def _load_db_keys() -> set[tuple[str, str]]:
    if not DB_PATH.exists():
        return set()
    connection = sqlite3.connect(DB_PATH)
    try:
        rows = connection.execute("select title, artist from songs").fetchall()
    finally:
        connection.close()
    return {_identity_key(title, artist) for title, artist in rows}


def _interleave(groups: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    longest = max((len(group) for group in groups), default=0)
    for index in range(longest):
        for group in groups:
            if index < len(group):
                output.append(group[index])
    return output


def _clean_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _identity_key(title: Any, artist: Any) -> tuple[str, str]:
    return (_normalize_identity(title), _normalize_identity(artist))


def _normalize_identity(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold()
    text = text.replace("&", " and ")
    text = re.sub(r"\b(remaster(?:ed)?|live|acoustic|sped up|slowed|nightcore|cover|version|edit)\b", " ", text)
    text = re.sub(r"[^0-9a-z가-힣]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _infer_theme(title: str) -> str:
    normalized = _normalize_identity(title)
    if any(word in normalized for word in ["love", "kiss", "heart", "body", "animals"]):
        return "relationship desire, emotional pull, or romantic tension"
    if any(word in normalized for word in ["texas", "atlanta", "boston", "stateside", "home"]):
        return "place identity, movement, or belonging"
    if any(word in normalized for word in ["golden", "red", "pinky", "hooligan", "fya"]):
        return "bold self-presentation and high-color attitude"
    if any(word in normalized for word in ["swim", "drop", "risk", "dracula"]):
        return "immersion, danger, or dramatic escalation"
    if any(word in normalized for word in ["easy", "normal", "know", "whisper"]):
        return "direct emotional statement and conversational intimacy"
    return "current pop identity, emotion, or attitude statement"


def _speaker_for_theme(theme: str) -> str:
    if "relationship" in theme:
        return "A speaker pulled toward someone, framing desire or conflict through a compact title image."
    if "place" in theme:
        return "A speaker using place, movement, or home imagery to anchor identity."
    if "bold" in theme:
        return "A confident speaker projecting color, attitude, and self-definition."
    if "danger" in theme or "immersion" in theme:
        return "A speaker leaning into intensity, risk, or a heightened emotional state."
    return "A contemporary pop speaker compressing the main feeling into a short title-centered cue."


def _short_cue(title: str) -> str:
    words = title.split()
    cue = " ".join(words[:8])
    return cue if len(words) <= 8 else f"{cue}..."


if __name__ == "__main__":
    main()
