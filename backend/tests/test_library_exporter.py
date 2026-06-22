import csv
import json

from app.services.library_exporter import export_library_by_genre


def test_export_library_by_genre_writes_csv_and_json(tmp_path) -> None:
    songs = [
        {
            "id": "song_1",
            "title": "Late Night",
            "artist": "A Singer",
            "genre": "K-pop Ballad",
            "country": "KR",
            "release_year": 2024,
            "bpm": 72,
            "key": "A major",
            "youtube_url": "https://youtube.com/watch?v=1",
            "youtube_metadata": {"title": "A Singer - Late Night", "channel_name": "A Singer"},
            "research_profile": {
                "identification": {"video_type": {"value": "official MV"}},
                "musical_features": {
                    "bpm": {"value": 72, "confidence": "medium"},
                    "key": {"value": "A major", "confidence": "medium"},
                    "hook_type": {"value": "title / lyric hook", "confidence": "medium"},
                    "lyric_theme": {"value": "이별과 그리움", "confidence": "medium"},
                },
            },
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
    ]
    analyses = [
        {
            "song_id": "song_1",
            "concept": {"mood": ["그리움", "회상"]},
            "lyrics": {"lyric_theme": "이별과 그리움"},
            "structure": {"structure": ["Intro", "Verse", "Chorus"], "first_chorus_time": 48},
            "harmony": {"chorus_progression": "IV - V - iii - vi"},
            "melody": {"chorus_peak_position": "chorus second half"},
            "hook": {"primary_hook_type": "title / lyric hook"},
            "arrangement": {"arrangement_build": "gradual layering"},
            "vocal": {"vocal_tone": "warm"},
            "mixing": {"vocal_position": "front"},
            "hit_factor": {"main_hit_factor": "clear chorus phrase"},
            "takeaway": {"transferable_principles": ["초반 절제"], "avoid_copying": ["멜로디 복제 금지"]},
            "audio_features": {"analysis_source": "youtube_link_research_profile_no_youtube_audio"},
        }
    ]

    manifest = export_library_by_genre(songs, analyses, tmp_path)

    all_csv = tmp_path / "all_songs.csv"
    genre_csv = tmp_path / "by_genre" / "K-pop_Ballad.csv"
    genre_index = tmp_path / "genre_index.csv"
    manifest_path = tmp_path / "export_manifest.json"

    assert all_csv.exists()
    assert genre_csv.exists()
    assert genre_index.exists()
    assert manifest_path.exists()
    assert manifest["total_songs"] == 1

    with all_csv.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    assert rows[0]["genre"] == "K-pop Ballad"
    assert rows[0]["hook_type"] == "title / lyric hook"
    assert rows[0]["transferable_principles"] == "초반 절제"

    stored_json = json.loads((tmp_path / "all_songs.json").read_text(encoding="utf-8"))
    assert stored_json[0]["title"] == "Late Night"
