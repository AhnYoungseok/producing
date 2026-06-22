from app.services.report_generator import build_hit_factor, build_takeaway, generate_full_report


def test_report_generator_connects_numbers_to_principles() -> None:
    sections = {
        "concept": {"mood": ["그리움"], "one_sentence_concept": "회상형 발라드"},
        "lyrics": {"story_flow": "상황에서 감정으로 상승", "lyric_point_of_view": "1인칭 화자"},
        "structure": {"structure": ["Intro", "Verse", "Chorus"], "first_chorus_time": 45},
        "harmony": {"chorus_progression": "IV - V - iii - vi"},
        "melody": {"creative_principle": "최고음 위치만 참고"},
        "hook": {"primary_hook_type": "lyric + melody hook", "hook_memorability": "high"},
        "arrangement": {"creative_principle": "레이어링 원리만 참고"},
        "vocal": {"creative_principle": "거리감만 참고"},
        "mixing": {"creative_principle": "공간감만 참고"},
    }
    audio = {"bpm": 72, "estimated_key": "A major", "onset_density": 1.2}
    sections["hit_factor"] = build_hit_factor(sections, audio)
    sections["takeaway"] = build_takeaway(sections)

    report = generate_full_report(sections, {"title": "Sample"}, audio)

    assert "72.0BPM" in report["summary"]
    assert "복제" in report["anti_copy_notice"]
    assert len(report["transferable_principles"]) >= 3
