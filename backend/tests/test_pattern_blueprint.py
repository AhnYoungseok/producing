from app.services.pattern_miner import extract_patterns
from app.services.song_blueprint_generator import generate_song_blueprint


def test_extract_patterns_from_analyses() -> None:
    songs = [
        {"id": "song_1", "genre": "K-pop Ballad", "bpm": 72, "key": "A major"},
        {"id": "song_2", "genre": "K-pop Ballad", "bpm": 76, "key": "A major"},
    ]
    analyses = [
        {
            "concept": {"mood": ["그리움", "회상"]},
            "lyrics": {"chorus_key_phrase_type": "직접 고백형"},
            "harmony": {"chorus_progression": "IV - V - iii - vi"},
            "hook": {"primary_hook_type": "lyric + melody hook"},
            "structure": {"structure": ["Intro", "Verse", "Chorus"]},
            "arrangement": {"arrangement_build": "gradual layering"},
        },
        {
            "concept": {"mood": ["그리움", "담담함"]},
            "lyrics": {"chorus_key_phrase_type": "직접 고백형"},
            "harmony": {"chorus_progression": "IV - V - iii - vi"},
            "hook": {"primary_hook_type": "lyric + melody hook"},
            "structure": {"structure": ["Intro", "Verse", "Chorus"]},
            "arrangement": {"arrangement_build": "gradual layering"},
        },
    ]

    patterns = extract_patterns(songs, analyses, ["concept", "harmony", "hook"])

    assert len(patterns) == 3
    assert patterns[0]["source_song_ids"] == ["song_1", "song_2"]
    assert "creative_use" in patterns[0]["pattern_json"]


def test_generate_song_blueprint_has_core_sections() -> None:
    project = {
        "title": "New Ballad",
        "target_genre": "K-pop Ballad",
        "target_mood": "그리움, 회상",
        "target_listener": "감성 발라드 청자",
        "reference_song_ids": ["song_1"],
        "theme": "늦은 밤의 회상",
        "bpm_range": "68-78",
        "vocal_style": "warm vocal",
    }
    songs = [{"id": "song_1", "genre": "K-pop Ballad", "bpm": 72, "key": "A major"}]
    analyses = [{"concept": {"mood": ["그리움"]}}]
    patterns = [{"description": "후렴 첫 두 마디에 핵심 감정을 배치"}]

    blueprint = generate_song_blueprint(project, songs, analyses, patterns)

    assert "concept" in blueprint
    assert "lyrics_plan" in blueprint
    assert "final_production_guide" in blueprint
    assert "복제하지" in blueprint["anti_copy_notice"]
