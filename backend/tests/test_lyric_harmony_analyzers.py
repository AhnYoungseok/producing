from app.services.harmony_analyzer import analyze_harmony
from app.services.lyric_analyzer import analyze_lyrics


def test_lyric_analyzer_extracts_repeated_hook_and_title_usage() -> None:
    lyrics = """
    [Verse]
    늦은 밤 창가에 혼자 남아
    괜찮은 척 웃어 보지만
    [Chorus]
    아직도 나는 그 밤에
    아직도 나는 그 밤에
    너를 기다려
    """

    result = analyze_lyrics(lyrics, title="아직도 나는 그 밤에")

    assert result["lyrics_provided"] is True
    assert result["core_message"] == "아직도 나는 그 밤에"
    assert result["title_usage"] == "후렴에 제목이 직접 등장"
    assert "아직도 나는 그 밤에" in result["repeated_key_phrases"]
    assert result["chorus_key_phrase_type"] == "제목 반복 후크"
    assert result["section_summary"]["chorus"].startswith("3줄")


def test_harmony_analyzer_parses_sections_and_harmonic_roles() -> None:
    chords = """
    Verse: I - V - vi - IV
    Pre-Chorus: ii - V - iii - vi
    Chorus: IV - V - iii - vi
    Bridge: ii - V/vi - vi
    """

    result = analyze_harmony(chords, {"estimated_key": "A major"})

    assert result["has_user_chords"] is True
    assert result["key"] == "A major"
    assert result["verse_progression"] == "I - V - vi - IV"
    assert result["pre_chorus_progression"] == "ii - V - iii - vi"
    assert result["chorus_progression"] == "IV - V - iii - vi"
    assert "V/vi" in result["secondary_dominants"]
    assert "IV" not in result["borrowed_chords"]
    assert result["section_functions"]["chorus"]["start_role"] == "감정을 여는 서브도미넌트"
    assert result["familiarity"]["level"] == "high"
