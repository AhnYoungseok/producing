from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from cloud_hit_song_batch import (
    LEDGER_PATH,
    _identity_hash,
    _load_ledger,
    _record_key,
    _record_keys,
    _save_cloud_exports,
    _save_ledger,
)


MUSICBRAINZ_API_URL = "https://musicbrainz.org/ws/2/recording"
MUSICBRAINZ_RECORDING_URL = "https://musicbrainz.org/recording"
MUSICBRAINZ_DOC_URL = "https://musicbrainz.org/doc/MusicBrainz_API"
SOURCE_TYPE = "musicbrainz_jazz_recording_bulk_backfill"
USER_AGENT = "HitSongLabJazzBackfill/1.0 (https://github.com/AhnYoungseok/producing)"

CURATED_ARTISTS = [
    "Miles Davis",
    "John Coltrane",
    "Ella Fitzgerald",
    "Louis Armstrong",
    "Duke Ellington",
    "Billie Holiday",
    "Thelonious Monk",
    "Charlie Parker",
    "Chet Baker",
    "Sarah Vaughan",
    "Nina Simone",
    "Count Basie",
    "Dizzy Gillespie",
    "Herbie Hancock",
    "Bill Evans",
    "Art Blakey",
    "Stan Getz",
    "Oscar Peterson",
    "Dave Brubeck",
    "Charles Mingus",
    "Sonny Rollins",
    "Wayne Shorter",
    "Cannonball Adderley",
    "Wes Montgomery",
    "Horace Silver",
    "Clifford Brown",
    "Lee Morgan",
    "Dexter Gordon",
    "Coleman Hawkins",
    "Lester Young",
    "Benny Goodman",
    "Glenn Miller",
    "Art Tatum",
    "Erroll Garner",
    "Benny Golson",
    "McCoy Tyner",
    "Keith Jarrett",
    "Chick Corea",
    "Pat Metheny",
    "Wynton Marsalis",
    "Diana Krall",
    "Norah Jones",
    "Esperanza Spalding",
    "Brad Mehldau",
    "Joshua Redman",
    "Kenny Burrell",
    "Joe Henderson",
    "Freddie Hubbard",
    "Milt Jackson",
    "Modern Jazz Quartet",
    "Gerry Mulligan",
    "Stanley Turrentine",
    "Grant Green",
    "Hank Mobley",
    "Bud Powell",
    "Fats Waller",
    "Jelly Roll Morton",
    "Sidney Bechet",
    "Bessie Smith",
    "Etta James",
    "Mel Torme",
    "Nat King Cole",
    "Frank Sinatra",
    "Peggy Lee",
    "Julie London",
    "Anita O'Day",
    "Blossom Dearie",
    "Toots Thielemans",
    "Antonio Carlos Jobim",
    "Joao Gilberto",
    "Astrud Gilberto",
    "Sergio Mendes",
    "Gilberto Gil",
]

STANDARD_TITLE_QUERIES = [
    "Autumn Leaves",
    "All the Things You Are",
    "Body and Soul",
    "Round Midnight",
    "Take Five",
    "So What",
    "My Funny Valentine",
    "Blue in Green",
    "Misty",
    "Summertime",
    "Fly Me to the Moon",
    "Stella by Starlight",
    "Giant Steps",
    "A Night in Tunisia",
    "Cherokee",
    "Caravan",
    "Take the A Train",
    "In a Sentimental Mood",
    "Satin Doll",
    "Lush Life",
    "Naima",
    "Moanin'",
    "Watermelon Man",
    "Cantaloupe Island",
    "Song for My Father",
    "Blue Monk",
    "Freddie Freeloader",
    "Straight No Chaser",
    "There Will Never Be Another You",
    "Have You Met Miss Jones",
    "The Girl from Ipanema",
    "Desafinado",
    "Corcovado",
    "Wave",
    "Blue Bossa",
    "Dolphin Dance",
    "Maiden Voyage",
    "Goodbye Pork Pie Hat",
    "Footprints",
    "Donna Lee",
    "Ornithology",
    "Confirmation",
]

BAD_TITLE_RE = re.compile(
    r"\b("
    r"alternate|alt\.?|take\s*\d+|false start|outtake|rehearsal|demo|"
    r"remaster(?:ed)?|mono|stereo|radio edit|single edit|edit|version|mix|"
    r"interview|spoken|announcement|intro|introduction|dialogue|applause|"
    r"live at|live in|live from|live on|karaoke|backing track"
    r")\b",
    re.IGNORECASE,
)

DESCRIPTOR_RE = re.compile(
    r"\s*[\(\[][^)\]]*(?:alternate|take|false start|outtake|rehearsal|demo|remaster|mono|stereo|edit|version|mix|live|spoken|intro|applause)[^)\]]*[\)\]]",
    re.IGNORECASE,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill jazz standards and jazz recording references from MusicBrainz metadata.")
    parser.add_argument("--add-count", type=int, default=10000)
    parser.add_argument("--ledger-path", default=str(LEDGER_PATH))
    parser.add_argument("--cache-dir", default="data/cache/musicbrainz_jazz")
    parser.add_argument("--request-delay", type=float, default=1.05)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ledger_path = Path(args.ledger_path)
    ledger = _load_ledger(ledger_path)
    existing_keys = _record_keys(ledger.get("songs", []))
    baseline_hashes = set(ledger.get("baseline", {}).get("identity_hashes", []))

    records = collect_musicbrainz_records(
        cache_dir=Path(args.cache_dir),
        delay=args.request_delay,
        needed=args.add_count if args.dry_run else max(args.add_count * 2, args.add_count + 2500),
    )
    new_rows: list[dict[str, Any]] = []
    seen_keys = set(existing_keys)
    seen_hashes = set(baseline_hashes)

    for record in records:
        row = build_row(record)
        key = _record_key(row)
        row_hash = _identity_hash(row["title"], row["artist"])
        if key in seen_keys or row_hash in seen_hashes:
            continue
        seen_keys.add(key)
        seen_hashes.add(row_hash)
        new_rows.append(row)
        if len(new_rows) >= args.add_count:
            break

    summary = {
        "source": MUSICBRAINZ_DOC_URL,
        "source_type": SOURCE_TYPE,
        "candidate_rows": len(records),
        "new_rows": len(new_rows),
        "current_total_before": ledger.get("total_after_baseline", len(ledger.get("songs", []))),
        "youtube_policy": "YouTube search links only; no audio download, extraction, capture, conversion, separation, or analysis.",
        "lyrics_policy": "No copyrighted lyrics stored. Lyric and hook notes are newly written metadata summaries.",
        "musical_confidence": "Chord progressions are jazz-style reference templates inferred from metadata; they are not transcriptions of MusicBrainz recordings.",
    }

    if args.dry_run:
        print_json({**summary, "sample": [f"{row['title']} - {row['artist']}" for row in new_rows[:20]]})
        return

    if len(new_rows) < args.add_count:
        raise RuntimeError(f"Only found {len(new_rows)} unique new jazz rows; requested {args.add_count}.")

    songs = ledger.get("songs", [])
    merged = [*songs, *new_rows]
    updated = {
        **ledger,
        "version": 1,
        "updated_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "total_after_baseline": int(ledger.get("baseline", {}).get("count", 0)) + len(merged),
        "songs": merged,
    }
    _save_ledger(ledger_path, updated)
    _save_cloud_exports(updated)
    print_json({**summary, "total_after_baseline": updated["total_after_baseline"]})


def collect_musicbrainz_records(*, cache_dir: Path, delay: float, needed: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    queries: list[tuple[str, int]] = []
    queries.extend((f'artist:"{artist}" AND tag:jazz', 100) for artist in CURATED_ARTISTS)
    queries.extend((f'recording:"{title}" AND tag:jazz', 50) for title in STANDARD_TITLE_QUERIES)
    queries.extend(("tag:jazz", 100) for _ in range(130))

    broad_offset = 0
    for index, (query, limit) in enumerate(queries):
        offset = broad_offset if query == "tag:jazz" else 0
        if query == "tag:jazz":
            broad_offset += limit
        payload = fetch_query(query, limit=limit, offset=offset, cache_dir=cache_dir, delay=delay if index else 0)
        for record in payload.get("recordings", []):
            clean = normalize_record(record, query=query, source_offset=offset)
            if clean:
                records.append(clean)
        if len(records) >= needed:
            break
    return rank_records(records)


def fetch_query(query: str, *, limit: int, offset: int, cache_dir: Path, delay: float) -> dict[str, Any]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha1(f"{query}_{limit}_{offset}".encode("utf-8")).hexdigest()
    cache_path = cache_dir / f"{cache_key}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    if delay:
        time.sleep(delay)
    params = urlencode({"query": query, "fmt": "json", "limit": limit, "offset": offset})
    request = Request(f"{MUSICBRAINZ_API_URL}?{params}", headers={"User-Agent": USER_AGENT})
    data = None
    for attempt in range(1, 7):
        try:
            with urlopen(request, timeout=60) as response:
                data = json.load(response)
            break
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == 6:
                raise
            time.sleep(min(60, 5 * attempt))
        except URLError:
            if attempt == 6:
                raise
            time.sleep(min(60, 5 * attempt))
    if data is None:
        raise RuntimeError(f"MusicBrainz request failed for query={query!r}, offset={offset}")
    cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def normalize_record(record: dict[str, Any], *, query: str, source_offset: int) -> dict[str, Any] | None:
    title = clean_title(record.get("title"))
    artist = artist_credit(record)
    if not title or not artist:
        return None
    raw_title = str(record.get("title") or "")
    if BAD_TITLE_RE.search(raw_title) or BAD_TITLE_RE.search(title):
        return None
    if len(title) < 2 or len(title) > 90 or len(artist) > 90:
        return None
    if title.lower() in {"intro", "introduction", "finale", "untitled"}:
        return None
    tags = [tag.get("name") for tag in record.get("tags", []) if tag.get("name")]
    return {
        "musicbrainz_id": record.get("id"),
        "title": title,
        "artist": artist,
        "first_release_date": record.get("first-release-date") or "",
        "score": record.get("score") or 0,
        "tags": tags,
        "query": query,
        "source_offset": source_offset,
    }


def clean_title(value: Any) -> str:
    title = str(value or "").strip()
    title = DESCRIPTOR_RE.sub("", title)
    title = re.sub(r"\s+", " ", title).strip(" -/:;")
    return title


def artist_credit(record: dict[str, Any]) -> str:
    parts = record.get("artist-credit") or []
    names = []
    for part in parts:
        if isinstance(part, dict):
            names.append(str(part.get("name") or ""))
            joinphrase = str(part.get("joinphrase") or "")
            if joinphrase and joinphrase.strip() not in {",", "&"}:
                names.append(joinphrase)
            elif joinphrase:
                names.append(joinphrase + " ")
        elif isinstance(part, str):
            names.append(part)
    artist = "".join(names).strip()
    return re.sub(r"\s+", " ", artist)


def rank_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        key = (compact_key(record["title"]), compact_key(record["artist"]))
        current = deduped.get(key)
        if current is None or record_score(record) > record_score(current):
            deduped[key] = record
    return sorted(deduped.values(), key=record_score, reverse=True)


def compact_key(value: str) -> str:
    return re.sub(r"[\W_]+", "", value.casefold(), flags=re.UNICODE)


def record_score(record: dict[str, Any]) -> float:
    score = float(record.get("score") or 0)
    query = str(record.get("query") or "")
    title = str(record.get("title") or "")
    artist = str(record.get("artist") or "")
    tags = " ".join(record.get("tags") or [])
    if query.startswith("artist:"):
        score += 50
    if query.startswith("recording:"):
        score += 65
    if any(name.casefold() in artist.casefold() for name in CURATED_ARTISTS):
        score += 35
    if any(title.casefold() == standard.casefold() for standard in STANDARD_TITLE_QUERIES):
        score += 40
    if "jazz" in tags.casefold():
        score += 15
    if record.get("first_release_date"):
        score += 3
    return score - float(record.get("source_offset") or 0) * 0.001


def build_row(record: dict[str, Any]) -> dict[str, Any]:
    title = record["title"]
    artist = record["artist"]
    release_year = release_year_from(record.get("first_release_date"))
    style = jazz_style(title, artist, record.get("tags") or [])
    chord = jazz_chord_template(style)
    youtube_query = quote_plus(f"{artist} {title} jazz official")
    chart_line = f"MusicBrainz jazz-tagged recording, relevance score {record.get('score', 0)}"
    return {
        "added_date": today_label(),
        "added_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "title": title,
        "artist": artist,
        "genre": style["genre"],
        "country": style["country"],
        "release_year": release_year,
        "youtube_url": f"https://www.youtube.com/results?search_query={youtube_query}",
        "bpm": None,
        "key": None,
        "chord_progression": chord,
        "structure": style["structure"],
        "hook_type": style["hook_type"],
        "hook_location": "head melody, turnaround, solo-entry cue, or vocal refrain depending on arrangement",
        "hook_cue": style["hook_cue"],
        "lyric_theme": style["lyric_theme"],
        "speaker_situation": style["speaker_situation"],
        "story_flow": style["story_flow"],
        "title_usage": "title usually functions as the head/theme cue; verify manually before quoting or adapting",
        "core_message": style["core_message"],
        "why_hook_works": style["why_hook_works"],
        "producer_takeaway": style["producer_takeaway"],
        "arrangement": style["arrangement"],
        "vocal": style["vocal"],
        "mixing": "warm midrange, present lead instrument/vocal, natural room or plate ambience; avoid over-quantized feel",
        "hit_factor": f"Real MusicBrainz recording metadata. {chart_line}. Use as jazz repertoire/reference signal, not as a sales chart claim.",
        "data_confidence": "medium-low",
        "musical_feature_confidence": "low; jazz harmony template inferred from metadata, not an audio transcription",
        "chart_source": "MusicBrainz recording search: jazz-tagged recordings",
        "chart_rank": None,
        "source_type": SOURCE_TYPE,
        "source_url": f"{MUSICBRAINZ_RECORDING_URL}/{record.get('musicbrainz_id')}" if record.get("musicbrainz_id") else MUSICBRAINZ_DOC_URL,
        "musicbrainz_recording_id": record.get("musicbrainz_id"),
        "musicbrainz_score": record.get("score"),
        "musicbrainz_tags": ", ".join(record.get("tags") or [])[:240],
    }


def release_year_from(value: Any) -> int | None:
    match = re.search(r"(18|19|20)\d{2}", str(value or ""))
    return int(match.group(0)) if match else None


def today_label() -> str:
    now = datetime.now()
    return f"{now.year}.{now.month}.{now.day}"


def jazz_style(title: str, artist: str, tags: list[str]) -> dict[str, str]:
    text = f"{title} {artist} {' '.join(tags)}".casefold()
    if any(term in text for term in ["bossa", "samba", "ipanema", "desafinado", "corcovado", "jobim", "gilberto"]):
        return {
            "genre": "Jazz Bossa Nova / Latin Standard",
            "country": "BR/US/Global",
            "structure": "AABA or ABAC song form with bossa/latin groove, head-solo-head performance logic",
            "hook_type": "smooth title/theme hook + ii-V-I color cadence",
            "hook_cue": "laid-back melody against extended major/minor seventh harmony",
            "lyric_theme": "romantic observation, distance, city/sea/season imagery; no lyrics stored",
            "speaker_situation": "cool, observant narrator with understated longing",
            "story_flow": "scene image -> understated desire -> harmonic color turn -> relaxed refrain return",
            "core_message": "beauty and distance can carry more emotion than direct confession",
            "why_hook_works": "bossa standards linger through a relaxed melodic cell over sophisticated but circular harmony.",
            "producer_takeaway": "Use nylon guitar or brushed kit feel, maj9/min9 voicings, and a restrained vocal/instrumental lead.",
            "arrangement": "bossa pulse, light percussion, bass in two, guitar/piano comping, tasteful solo section",
            "vocal": "soft, conversational, slightly behind the beat if vocal-led",
        }
    if any(term in text for term in ["blue", "blues", "freddie freeloader", "straight no chaser", "bag's groove"]):
        return {
            "genre": "Jazz Blues / Hard Bop",
            "country": "US/Global",
            "structure": "12-bar jazz blues or blues-derived head-solo-head form",
            "hook_type": "riff/head hook + dominant turnaround",
            "hook_cue": "short blues motif answered by horn/piano phrase",
            "lyric_theme": "resilience, wit, late-night tension; often instrumental metadata only",
            "speaker_situation": "streetwise narrator or instrumental voice turning pain into swing",
            "story_flow": "riff statement -> call/response -> solo chorus lift -> final riff return",
            "core_message": "a simple motif becomes deep when the harmony keeps turning underneath",
            "why_hook_works": "jazz blues hooks are compact, repeatable, and flexible enough for improvisation.",
            "producer_takeaway": "Build a strong two-bar riff and let altered dominants add sophistication at the turnaround.",
            "arrangement": "walking bass, ride cymbal, piano/guitar comping, horn or vocal head, solo trades",
            "vocal": "earthy, behind-the-beat phrasing if vocal-led",
        }
    if any(term in text for term in ["giant steps", "coltrane", "parker", "donna lee", "ornithology", "confirmation", "bebop"]):
        return {
            "genre": "Bebop / Post-Bop Jazz Standard",
            "country": "US/Global",
            "structure": "fast head-solo-head form with dense ii-V chains or Coltrane-style cycles",
            "hook_type": "bebop head melody + rapid harmonic turnaround",
            "hook_cue": "angular melodic cell over fast-moving dominants",
            "lyric_theme": "instrumental virtuosity, motion, chase, wit; no lyrics stored",
            "speaker_situation": "restless instrumental narrator pushing through complex changes",
            "story_flow": "head theme -> high-density harmonic motion -> solos -> compressed final head",
            "core_message": "forward motion itself becomes the emotional hook",
            "why_hook_works": "bebop heads make complexity memorable by locking fast harmony to a clear melodic contour.",
            "producer_takeaway": "Use chromatic approach tones and ii-V chains, but keep the top-line motif singable.",
            "arrangement": "uptempo swing, horn lead, piano comping, walking bass, drum accents and trades",
            "vocal": "scat-like agility or instrumental phrasing emphasis",
        }
    if any(term in text for term in ["so what", "maiden voyage", "footprints", "dolphin dance", "hancock", "shorter", "tyner", "modal"]):
        return {
            "genre": "Modal / Modern Jazz Classic",
            "country": "US/Global",
            "structure": "modal vamp or open-form head-solo-head with spacious harmonic rhythm",
            "hook_type": "modal motif + pedal/vamp hook",
            "hook_cue": "small melodic idea repeated over suspended harmony",
            "lyric_theme": "space, search, atmosphere, ambiguity; often instrumental metadata only",
            "speaker_situation": "inward, exploratory narrator floating over a tonal center",
            "story_flow": "vamp atmosphere -> theme statement -> modal solo expansion -> theme return",
            "core_message": "one color can be enough if the rhythm and melody breathe",
            "why_hook_works": "modal classics are memorable because harmony stays open while the motif becomes iconic.",
            "producer_takeaway": "Use sus chords, quartal voicings, pedal bass, and space; do not over-resolve too early.",
            "arrangement": "modal vamp, sparse comping, bass pedal, cymbal shimmer, long solo arcs",
            "vocal": "minimal, airy, mantra-like if vocal-led",
        }
    if any(term in text for term in ["ella", "billie", "sarah", "sinatra", "nat king cole", "peggy lee", "diana krall", "norah jones", "vaughan", "holiday"]):
        return {
            "genre": "Vocal Jazz Standard / Jazz Ballad",
            "country": "US/Global",
            "structure": "AABA/ABAC standard form with vocal head, instrumental response, and final tag",
            "hook_type": "title lyric refrain + jazz cadence hook",
            "hook_cue": "title phrase lands on maj7/6/9 color or ii-V-I resolution",
            "lyric_theme": "love, loss, longing, memory, elegance; no lyrics stored",
            "speaker_situation": "mature narrator saying less while implying more",
            "story_flow": "intimate opening -> title refrain -> harmonic lift -> late tag or turnaround",
            "core_message": "restraint makes the emotional line more durable",
            "why_hook_works": "vocal standards tie memorable title phrases to elegant cadences and flexible rubato phrasing.",
            "producer_takeaway": "Let the singer sit slightly behind the beat and give the cadence room to bloom.",
            "arrangement": "piano trio or small ensemble, brushed drums, double bass, optional horn response",
            "vocal": "close, warm, conversational, controlled vibrato and delayed phrasing",
        }
    if any(term in text for term in ["duke", "ellington", "basie", "goodman", "miller", "swing", "take the a train", "satin doll", "caravan"]):
        return {
            "genre": "Swing / Big Band Jazz Classic",
            "country": "US/Global",
            "structure": "32-bar swing standard or big-band head arrangement with sectional answers",
            "hook_type": "swing riff + title/head melody hook",
            "hook_cue": "brass/reed riff or title motif with strong rhythmic identity",
            "lyric_theme": "urban motion, elegance, dance, wit; often instrumental metadata only",
            "speaker_situation": "public, stylish narrator moving through a room or city",
            "story_flow": "riff intro -> head -> sectional response -> solo feature -> shout/tag",
            "core_message": "rhythm and ensemble identity can make a title feel iconic",
            "why_hook_works": "swing classics turn short riffs into social memory through orchestration and groove.",
            "producer_takeaway": "Use call-and-response voicing and a riff that survives even if stripped to piano and bass.",
            "arrangement": "swing rhythm section, brass/reed answers, shout chorus, featured solo",
            "vocal": "clear, rhythmic, smile in the tone if vocal-led",
        }
    return {
        "genre": "Jazz Standard / Classic Recording Reference",
        "country": "US/Global",
        "structure": "head-solo-head or AABA/ABAC standard form with improvised middle section",
        "hook_type": "head melody + ii-V-I turnaround hook",
        "hook_cue": "memorable theme supported by extended seventh/ninth chord movement",
        "lyric_theme": "love, memory, motion, night, resilience, or instrumental mood; no lyrics stored",
        "speaker_situation": "mature musical narrator balancing restraint and harmonic color",
        "story_flow": "theme statement -> harmonic variation/solo -> return with tag or cadence",
        "core_message": "a clear motif can carry sophisticated harmony without losing emotional directness",
        "why_hook_works": "classic jazz recordings make harmony memorable through recurring heads, cadences, and performance identity.",
        "producer_takeaway": "Use jazz changes as emotional architecture, then simplify the top-line so the song still feels immediate.",
        "arrangement": "small ensemble or vocal trio setting, brushed or swinging drums, acoustic bass, piano/guitar comping",
        "vocal": "phrased like an instrument; leave space before important title words if vocal-led",
    }


def jazz_chord_template(style: dict[str, str]) -> str:
    genre = style["genre"].casefold()
    if "blues" in genre:
        return "Jazz blues in F: | F7 | Bb7 | F7 | Cm7 F7 | Bb7 | Bdim7 | F7/A D7alt | Gm7 C7 | Am7 D7alt | Gm7 C7 | F7 D7alt | Gm7 C7alt |. Use shell voicings, guide-tone lines, and altered V chords; template only, not a transcription."
    if "bossa" in genre or "latin" in genre:
        return "Bossa/Latin standard color in C: | Dm9 G13 | Cmaj9 A7alt | Dm9 G13 | C6/9 | F#m7b5 B7b9 | Em9 A13 | Dm9 G13 | C6/9 |. Add chromatic bass approach and nylon-guitar syncopation; template only."
    if "bebop" in genre or "post-bop" in genre:
        return "Bebop ii-V chain: | Cmaj7 A7alt | Dm7 G7alt | Em7 A7alt | Dm7 G7 | Cmaj7 C#dim7 | Dm7 G7 | Em7 A7alt | Dm7 G7alt |. Optional Coltrane color: | Bmaj7 D7 | Gmaj7 Bb7 | Ebmaj7 | Am7 D7 |. Template only."
    if "modal" in genre:
        return "Modal jazz layer: | Dm11 | Dm11 | Dm11 | Dm11 | Ebm11 | Ebm11 | Dm11 | Dm11 |, plus suspended color | Csus13 | Fsus13 |. Keep pedal bass, quartal voicings, and slow harmonic rhythm; template only."
    if "swing" in genre or "big band" in genre:
        return "Swing/rhythm-changes reference in Bb: A | Bb6 G7 | Cm7 F7 | Dm7 G7 | Cm7 F7 | Bb6 Bb7 | Eb6 Edim7 | Bb/F G7 | Cm7 F7 |; Bridge | D7 | G7 | C7 | F7 |. Use riff answers and shout-chorus lift; template only."
    if "vocal" in genre or "ballad" in genre:
        return "Vocal jazz ballad in Eb: | Ebmaj9 Cm9 | Fm9 Bb13 | Gm7 C7alt | Fm9 Bb13 | Abmaj7 Abm6 | Gm7 C7b9 | Fm9 Bb13 | Eb6/9 |. Add backdoor cadence | Abm9 Db13 | Ebmaj9 | for mature release; template only."
    return "Jazz standard core in C: | Cmaj9 A7alt | Dm9 G13 | Em7 A7alt | Dm9 G13 | Fmaj9 Fm9 | Em7 A7b9 | Dm9 G13 | C6/9 |. Add tritone substitute | Dm9 Db13 | Cmaj9 | and turnaround | Em7 A7alt Dm9 G13 |. Template only, not a transcription."


def print_json(value: dict[str, Any]) -> None:
    sys.stdout.buffer.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
