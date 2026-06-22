from app.services.statistics_service import build_hit_song_statistics


def test_statistics_answers_core_composer_questions() -> None:
    songs = [
        {"id": "song_1", "genre": "K-pop Ballad", "country": "KR", "release_year": 2010, "bpm": 72, "key": "A major"},
        {"id": "song_2", "genre": "K-pop Ballad", "country": "KR", "release_year": 2020, "bpm": 76, "key": "A major"},
    ]
    analyses = [
        _analysis("song_1", 52),
        _analysis("song_2", 48),
    ]

    stats = build_hit_song_statistics(songs, analyses)

    assert stats["summary"]["average_bpm"] == 74
    assert stats["summary"]["average_first_chorus_time"] == 50
    assert stats["by_genre"][0]["label"] == "K-pop Ballad"
    assert stats["top_chorus_progressions"][0]["label"] == "IV - V - iii - vi"
    assert stats["hook_type_distribution"][0]["label"] == "lyric + melody hook"
    assert len(stats["composer_questions"]) >= 6


def test_statistics_exposes_chart_pattern_and_feature_schema() -> None:
    songs = [
        {"id": "song_1", "genre": "K-pop Ballad", "country": "KR", "release_year": 2010, "bpm": 72, "key": "A major"},
        {"id": "song_2", "genre": "K-pop Ballad", "country": "KR", "release_year": 2020, "bpm": 76, "key": "A major"},
    ]
    analyses = [_analysis("song_1", 52), _analysis("song_2", 48)]

    stats = build_hit_song_statistics(songs, analyses)

    assert "chart_datasets" in stats
    assert "by_genre" in stats["chart_datasets"]
    assert stats["chart_datasets"]["hook_type_distribution"]["items"][0]["label"] == "lyric + melody hook"
    assert len(stats["pattern_summaries"]) >= 6
    assert stats["pattern_summaries"][0]["producer_takeaway"]
    assert any(group["category"] == "Chord and Structure Analysis" for group in stats["feature_schema"])


def _analysis(song_id: str, first_chorus_time: int) -> dict:
    return {
        "song_id": song_id,
        "concept": {"mood": ["그리움", "회상"]},
        "lyrics": {"chorus_key_phrase_type": "직접 고백형", "title_usage": "후렴 첫 줄"},
        "structure": {
            "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Final Chorus"],
            "first_chorus_time": first_chorus_time,
            "final_chorus_expansion": "adlib + strings",
        },
        "harmony": {"chorus_progression": "IV - V - iii - vi"},
        "melody": {"chorus_peak_position": "chorus second half", "motif_type": "short repeated phrase"},
        "hook": {"primary_hook_type": "lyric + melody hook"},
        "arrangement": {"arrangement_build": "gradual layering", "final_chorus_lift": "strings + adlibs"},
        "vocal": {"vocal_tone": "warm", "chorus_delivery": "open and powerful"},
        "mixing": {"vocal_position": "front", "stereo_width": "wide"},
        "hit_factor": {"main_hit_factor": "clear chorus key phrase", "replay_factor": "high"},
    }
