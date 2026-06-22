import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class SQLiteStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def init_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS songs (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    artist TEXT,
                    genre TEXT,
                    release_year INTEGER,
                    country TEXT,
                    youtube_url TEXT,
                    youtube_metadata_json TEXT,
                    research_profile_json TEXT,
                    file_name TEXT,
                    duration REAL,
                    bpm REAL,
                    key TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS song_analyses (
                    id TEXT PRIMARY KEY,
                    song_id TEXT NOT NULL,
                    concept_json TEXT NOT NULL,
                    lyrics_json TEXT NOT NULL,
                    structure_json TEXT NOT NULL,
                    harmony_json TEXT NOT NULL,
                    melody_json TEXT NOT NULL,
                    hook_json TEXT NOT NULL,
                    rhythm_json TEXT NOT NULL,
                    arrangement_json TEXT NOT NULL,
                    vocal_json TEXT NOT NULL,
                    mixing_json TEXT NOT NULL,
                    hit_factor_json TEXT NOT NULL,
                    takeaway_json TEXT NOT NULL,
                    full_report_json TEXT NOT NULL,
                    audio_features_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(song_id) REFERENCES songs(id)
                );

                CREATE TABLE IF NOT EXISTS patterns (
                    id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    genre TEXT,
                    description TEXT NOT NULL,
                    source_song_ids TEXT NOT NULL,
                    pattern_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    target_genre TEXT,
                    target_mood TEXT,
                    target_listener TEXT,
                    reference_song_ids TEXT NOT NULL,
                    theme TEXT,
                    vocal_style TEXT,
                    bpm_range TEXT,
                    lyric_language TEXT,
                    instruments TEXT,
                    arrangement_style TEXT,
                    concept_json TEXT NOT NULL,
                    lyrics_plan_json TEXT NOT NULL,
                    harmony_plan_json TEXT NOT NULL,
                    melody_plan_json TEXT NOT NULL,
                    hook_plan_json TEXT NOT NULL,
                    arrangement_plan_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS song_blueprints (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    blueprint_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                );
                """
            )
            self._ensure_column(connection, "songs", "youtube_metadata_json", "TEXT")
            self._ensure_column(connection, "songs", "research_profile_json", "TEXT")
            connection.commit()

    def create_song(self, data: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        song_id = data.get("id") or make_id("song")
        duplicate = self.find_song_by_identity(data.get("title") or "Untitled Song", data.get("artist"))
        if duplicate and duplicate["id"] != song_id:
            return duplicate
        row = {
            "id": song_id,
            "title": data.get("title") or "Untitled Song",
            "artist": data.get("artist"),
            "genre": data.get("genre"),
            "release_year": data.get("release_year"),
            "country": data.get("country"),
            "youtube_url": data.get("youtube_url"),
            "youtube_metadata_json": json.dumps(data.get("youtube_metadata", {}), ensure_ascii=False),
            "research_profile_json": json.dumps(data.get("research_profile", {}), ensure_ascii=False),
            "file_name": data.get("file_name"),
            "duration": data.get("duration"),
            "bpm": data.get("bpm"),
            "key": data.get("key"),
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO songs (
                    id, title, artist, genre, release_year, country, youtube_url, youtube_metadata_json, research_profile_json,
                    file_name, duration, bpm, key, created_at, updated_at
                )
                VALUES (
                    :id, :title, :artist, :genre, :release_year, :country, :youtube_url, :youtube_metadata_json, :research_profile_json,
                    :file_name, :duration, :bpm, :key, :created_at, :updated_at
                )
                """,
                row,
            )
            connection.commit()
        return self.get_song(song_id) or row

    def find_song_by_identity(self, title: str, artist: str | None) -> dict[str, Any] | None:
        title_key = normalize_song_title(title)
        artist_key = normalize_artist_name(artist)
        if not title_key:
            return None
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM songs").fetchall()
        for row in rows:
            song = self._song_row_to_dict(row)
            if normalize_song_title(song.get("title") or "") != title_key:
                continue
            if normalize_artist_name(song.get("artist")) == artist_key:
                return song
        return None

    def update_song_audio_summary(self, song_id: str, summary: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE songs
                SET file_name = COALESCE(:file_name, file_name),
                    duration = :duration,
                    bpm = COALESCE(:bpm, bpm),
                    key = COALESCE(:key, key),
                    updated_at = :updated_at
                WHERE id = :id
                """,
                {
                    "id": song_id,
                    "file_name": summary.get("file_name"),
                    "duration": summary.get("duration"),
                    "bpm": summary.get("bpm"),
                    "key": summary.get("key"),
                    "updated_at": utc_now(),
                },
            )
            connection.commit()

    def update_song_research_profile(self, song_id: str, profile: dict[str, Any]) -> None:
        identification = profile.get("identification", {})
        features = profile.get("musical_features", {})
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE songs
                SET title = COALESCE(:title, title),
                    artist = COALESCE(:artist, artist),
                    genre = COALESCE(:genre, genre),
                    release_year = COALESCE(:release_year, release_year),
                    country = COALESCE(:country, country),
                    youtube_metadata_json = :youtube_metadata_json,
                    research_profile_json = :research_profile_json,
                    bpm = :bpm,
                    key = :key,
                    updated_at = :updated_at
                WHERE id = :id
                """,
                {
                    "id": song_id,
                    "title": _confidence_value(identification.get("title")),
                    "artist": _confidence_value(identification.get("artist")),
                    "genre": _confidence_value(identification.get("genre")),
                    "release_year": _confidence_value(identification.get("release_year")),
                    "country": _confidence_value(identification.get("country")),
                    "youtube_metadata_json": json.dumps(profile.get("youtube_metadata", {}), ensure_ascii=False),
                    "research_profile_json": json.dumps(profile, ensure_ascii=False),
                    "bpm": _confidence_value(features.get("bpm")),
                    "key": _confidence_value(features.get("key")),
                    "updated_at": utc_now(),
                },
            )
            connection.commit()

    def list_songs(
        self,
        query: Optional[str] = None,
        genre: Optional[str] = None,
        key: Optional[str] = None,
        country: Optional[str] = None,
        emotion: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: dict[str, Any] = {}
        if query:
            clauses.append("(LOWER(s.title) LIKE :query OR LOWER(COALESCE(s.artist, '')) LIKE :query)")
            values["query"] = f"%{query.lower()}%"
        if genre:
            clauses.append("s.genre = :genre")
            values["genre"] = genre
        if key:
            clauses.append("s.key = :key")
            values["key"] = key
        if country:
            clauses.append("s.country = :country")
            values["country"] = country
        if emotion:
            clauses.append("LOWER(COALESCE(a.concept_json, '')) LIKE :emotion")
            values["emotion"] = f"%{emotion.lower()}%"

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT s.*, CASE WHEN a.id IS NULL THEN 0 ELSE 1 END AS analysis_complete
                FROM songs s
                LEFT JOIN song_analyses a ON a.song_id = s.id
                {where_sql}
                ORDER BY s.created_at DESC
                """,
                values,
            ).fetchall()
        return [self._song_row_to_dict(row) for row in rows]

    def get_song(self, song_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT s.*, CASE WHEN a.id IS NULL THEN 0 ELSE 1 END AS analysis_complete
                FROM songs s
                LEFT JOIN song_analyses a ON a.song_id = s.id
                WHERE s.id = ?
                """,
                (song_id,),
            ).fetchone()
        return self._song_row_to_dict(row) if row else None

    def save_analysis(self, song_id: str, analysis: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        analysis_id = make_id("analysis")
        row = {
            "id": analysis_id,
            "song_id": song_id,
            "concept_json": json.dumps(analysis["concept"], ensure_ascii=False),
            "lyrics_json": json.dumps(analysis["lyrics"], ensure_ascii=False),
            "structure_json": json.dumps(analysis["structure"], ensure_ascii=False),
            "harmony_json": json.dumps(analysis["harmony"], ensure_ascii=False),
            "melody_json": json.dumps(analysis["melody"], ensure_ascii=False),
            "hook_json": json.dumps(analysis["hook"], ensure_ascii=False),
            "rhythm_json": json.dumps(analysis["rhythm"], ensure_ascii=False),
            "arrangement_json": json.dumps(analysis["arrangement"], ensure_ascii=False),
            "vocal_json": json.dumps(analysis["vocal"], ensure_ascii=False),
            "mixing_json": json.dumps(analysis["mixing"], ensure_ascii=False),
            "hit_factor_json": json.dumps(analysis["hit_factor"], ensure_ascii=False),
            "takeaway_json": json.dumps(analysis["takeaway"], ensure_ascii=False),
            "full_report_json": json.dumps(analysis["full_report"], ensure_ascii=False),
            "audio_features_json": json.dumps(analysis["audio_features"], ensure_ascii=False),
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as connection:
            connection.execute("DELETE FROM song_analyses WHERE song_id = ?", (song_id,))
            connection.execute(
                """
                INSERT INTO song_analyses (
                    id, song_id, concept_json, lyrics_json, structure_json, harmony_json,
                    melody_json, hook_json, rhythm_json, arrangement_json, vocal_json,
                    mixing_json, hit_factor_json, takeaway_json, full_report_json,
                    audio_features_json, created_at, updated_at
                )
                VALUES (
                    :id, :song_id, :concept_json, :lyrics_json, :structure_json, :harmony_json,
                    :melody_json, :hook_json, :rhythm_json, :arrangement_json, :vocal_json,
                    :mixing_json, :hit_factor_json, :takeaway_json, :full_report_json,
                    :audio_features_json, :created_at, :updated_at
                )
                """,
                row,
            )
            connection.commit()
        return self.get_analysis(song_id) or {}

    def get_analysis(self, song_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM song_analyses WHERE song_id = ?", (song_id,)).fetchone()
        return self._analysis_row_to_dict(row) if row else None

    def get_analyses_for_songs(self, song_ids: list[str]) -> list[dict[str, Any]]:
        if not song_ids:
            return []
        placeholders = ",".join("?" for _ in song_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM song_analyses WHERE song_id IN ({placeholders})",
                song_ids,
            ).fetchall()
        return [self._analysis_row_to_dict(row) for row in rows]

    def save_pattern(self, pattern: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        row = {
            "id": make_id("pattern"),
            "pattern_type": pattern["pattern_type"],
            "genre": pattern.get("genre"),
            "description": pattern["description"],
            "source_song_ids": json.dumps(pattern.get("source_song_ids", []), ensure_ascii=False),
            "pattern_json": json.dumps(pattern["pattern_json"], ensure_ascii=False),
            "created_at": now,
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO patterns (
                    id, pattern_type, genre, description, source_song_ids, pattern_json, created_at
                )
                VALUES (:id, :pattern_type, :genre, :description, :source_song_ids, :pattern_json, :created_at)
                """,
                row,
            )
            connection.commit()
        return self._pattern_row_to_dict(row)

    def list_patterns(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM patterns ORDER BY created_at DESC").fetchall()
        return [self._pattern_row_to_dict(row) for row in rows]

    def create_project(self, data: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        row = {
            "id": make_id("project"),
            "title": data["title"],
            "target_genre": data.get("target_genre"),
            "target_mood": data.get("target_mood"),
            "target_listener": data.get("target_listener"),
            "reference_song_ids": json.dumps(data.get("reference_song_ids", []), ensure_ascii=False),
            "theme": data.get("theme"),
            "vocal_style": data.get("vocal_style"),
            "bpm_range": data.get("bpm_range"),
            "lyric_language": data.get("lyric_language") or "한국어",
            "instruments": data.get("instruments"),
            "arrangement_style": data.get("arrangement_style"),
            "concept_json": json.dumps({}, ensure_ascii=False),
            "lyrics_plan_json": json.dumps({}, ensure_ascii=False),
            "harmony_plan_json": json.dumps({}, ensure_ascii=False),
            "melody_plan_json": json.dumps({}, ensure_ascii=False),
            "hook_plan_json": json.dumps({}, ensure_ascii=False),
            "arrangement_plan_json": json.dumps({}, ensure_ascii=False),
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO projects (
                    id, title, target_genre, target_mood, target_listener, reference_song_ids,
                    theme, vocal_style, bpm_range, lyric_language, instruments, arrangement_style,
                    concept_json, lyrics_plan_json, harmony_plan_json, melody_plan_json,
                    hook_plan_json, arrangement_plan_json, created_at, updated_at
                )
                VALUES (
                    :id, :title, :target_genre, :target_mood, :target_listener, :reference_song_ids,
                    :theme, :vocal_style, :bpm_range, :lyric_language, :instruments, :arrangement_style,
                    :concept_json, :lyrics_plan_json, :harmony_plan_json, :melody_plan_json,
                    :hook_plan_json, :arrangement_plan_json, :created_at, :updated_at
                )
                """,
                row,
            )
            connection.commit()
        return self.get_project(row["id"]) or {}

    def list_projects(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
        return [self._project_row_to_dict(row) for row in rows]

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return self._project_row_to_dict(row) if row else None

    def update_project_plans(self, project_id: str, plans: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE projects
                SET concept_json = :concept_json,
                    lyrics_plan_json = :lyrics_plan_json,
                    harmony_plan_json = :harmony_plan_json,
                    melody_plan_json = :melody_plan_json,
                    hook_plan_json = :hook_plan_json,
                    arrangement_plan_json = :arrangement_plan_json,
                    updated_at = :updated_at
                WHERE id = :id
                """,
                {
                    "id": project_id,
                    "concept_json": json.dumps(plans.get("concept", {}), ensure_ascii=False),
                    "lyrics_plan_json": json.dumps(plans.get("lyrics_plan", {}), ensure_ascii=False),
                    "harmony_plan_json": json.dumps(plans.get("harmony_plan", {}), ensure_ascii=False),
                    "melody_plan_json": json.dumps(plans.get("melody_plan", {}), ensure_ascii=False),
                    "hook_plan_json": json.dumps(plans.get("hook_plan", {}), ensure_ascii=False),
                    "arrangement_plan_json": json.dumps(plans.get("arrangement_plan", {}), ensure_ascii=False),
                    "updated_at": utc_now(),
                },
            )
            connection.commit()

    def save_blueprint(self, project_id: str, blueprint: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        row = {
            "id": make_id("blueprint"),
            "project_id": project_id,
            "blueprint_json": json.dumps(blueprint, ensure_ascii=False),
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as connection:
            connection.execute("DELETE FROM song_blueprints WHERE project_id = ?", (project_id,))
            connection.execute(
                """
                INSERT INTO song_blueprints (id, project_id, blueprint_json, created_at, updated_at)
                VALUES (:id, :project_id, :blueprint_json, :created_at, :updated_at)
                """,
                row,
            )
            connection.commit()
        return self.get_blueprint(project_id) or {}

    def get_blueprint(self, project_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM song_blueprints WHERE project_id = ?", (project_id,)).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "blueprint_json": json.loads(row["blueprint_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def dashboard(self) -> dict[str, Any]:
        songs = self.list_songs()
        patterns = self.list_patterns()
        projects = self.list_projects()
        bpms = [song["bpm"] for song in songs if song.get("bpm") is not None]
        keys = count_values(song.get("key") for song in songs)
        genres = count_values(song.get("genre") or "Unknown" for song in songs)
        analyses = self.get_analyses_for_songs([song["id"] for song in songs])
        hooks = count_values(analysis["hook"].get("primary_hook_type") for analysis in analyses)
        progressions = count_values(analysis["harmony"].get("chorus_progression") for analysis in analyses)
        structures = count_values(" - ".join(analysis["structure"].get("structure", [])) for analysis in analyses)
        return {
            "song_count": len(songs),
            "genre_counts": genres,
            "average_bpm": round(sum(bpms) / len(bpms), 2) if bpms else 0,
            "top_keys": keys[:5],
            "top_progressions": progressions[:5],
            "top_structures": structures[:5],
            "hook_distribution": hooks[:5],
            "recent_songs": songs[:5],
            "active_projects": projects[:5],
            "pattern_count": len(patterns),
        }

    @staticmethod
    def _ensure_column(connection: sqlite3.Connection, table: str, column: str, column_type: str) -> None:
        columns = [row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _song_row_to_dict(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        row_dict = dict(row)
        raw_metadata = row_dict.pop("youtube_metadata_json", None)
        raw_research_profile = row_dict.pop("research_profile_json", None)
        if raw_metadata:
            try:
                row_dict["youtube_metadata"] = json.loads(raw_metadata)
            except json.JSONDecodeError:
                row_dict["youtube_metadata"] = {}
        else:
            row_dict["youtube_metadata"] = {}
        if raw_research_profile:
            try:
                row_dict["research_profile"] = json.loads(raw_research_profile)
            except json.JSONDecodeError:
                row_dict["research_profile"] = {}
        else:
            row_dict["research_profile"] = {}
        return row_dict

    @staticmethod
    def _analysis_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "song_id": row["song_id"],
            "concept": json.loads(row["concept_json"]),
            "lyrics": json.loads(row["lyrics_json"]),
            "structure": json.loads(row["structure_json"]),
            "harmony": json.loads(row["harmony_json"]),
            "melody": json.loads(row["melody_json"]),
            "hook": json.loads(row["hook_json"]),
            "rhythm": json.loads(row["rhythm_json"]),
            "arrangement": json.loads(row["arrangement_json"]),
            "vocal": json.loads(row["vocal_json"]),
            "mixing": json.loads(row["mixing_json"]),
            "hit_factor": json.loads(row["hit_factor_json"]),
            "takeaway": json.loads(row["takeaway_json"]),
            "full_report": json.loads(row["full_report_json"]),
            "audio_features": json.loads(row["audio_features_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _pattern_row_to_dict(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        row_dict = dict(row)
        row_dict["source_song_ids"] = json.loads(row_dict["source_song_ids"])
        row_dict["pattern_json"] = json.loads(row_dict["pattern_json"])
        return row_dict

    @staticmethod
    def _project_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "title": row["title"],
            "target_genre": row["target_genre"],
            "target_mood": row["target_mood"],
            "target_listener": row["target_listener"],
            "reference_song_ids": json.loads(row["reference_song_ids"]),
            "theme": row["theme"],
            "vocal_style": row["vocal_style"],
            "bpm_range": row["bpm_range"],
            "lyric_language": row["lyric_language"],
            "instruments": row["instruments"],
            "arrangement_style": row["arrangement_style"],
            "concept_json": json.loads(row["concept_json"]),
            "lyrics_plan_json": json.loads(row["lyrics_plan_json"]),
            "harmony_plan_json": json.loads(row["harmony_plan_json"]),
            "melody_plan_json": json.loads(row["melody_plan_json"]),
            "hook_plan_json": json.loads(row["hook_plan_json"]),
            "arrangement_plan_json": json.loads(row["arrangement_plan_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


def init_database(database_path: Path) -> None:
    SQLiteStore(database_path).init_schema()


def count_values(values: Any) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for value in values:
        if not value:
            continue
        counts[str(value)] = counts.get(str(value), 0) + 1
    return [{"label": key, "count": value} for key, value in sorted(counts.items(), key=lambda item: item[1], reverse=True)]


def _confidence_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def normalize_song_title(value: str | None) -> str:
    text = (value or "").casefold()
    text = re.sub(r"\[[^\]]*(remaster|official|music video|lyric|lyrics|live|cover|mv|4k|hd|ver\.?|version)[^\]]*\]", " ", text)
    text = re.sub(r"\([^\)]*(remaster|official|music video|lyric|lyrics|live|cover|mv|4k|hd|ver\.?|version)[^\)]*\)", " ", text)
    text = re.sub(r"\b(official\s+music\s+video|official\s+mv|lyric\s+video|lyrics\s+video|4k\s+remaster|hd\s+remaster)\b", " ", text)
    return re.sub(r"[^0-9a-z가-힣]+", "", text)


def normalize_artist_name(value: str | None) -> str:
    text = (value or "").casefold()
    text = re.sub(r"\b(feat\.?|ft\.?|with)\b.*$", " ", text)
    return re.sub(r"[^0-9a-z가-힣]+", "", text)
