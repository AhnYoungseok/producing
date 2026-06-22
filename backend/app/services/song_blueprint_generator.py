from statistics import mean
from typing import Any


def generate_song_blueprint(project: dict[str, Any], songs: list[dict[str, Any]], analyses: list[dict[str, Any]], patterns: list[dict[str, Any]]) -> dict[str, Any]:
    genre = project.get("target_genre") or most_common(song.get("genre") for song in songs) or "K-pop Ballad"
    mood = project.get("target_mood") or infer_common_mood(analyses) or "그리움, 회상"
    bpm = infer_target_bpm(project.get("bpm_range"), songs)
    key = most_common(song.get("key") for song in songs) or "A major"
    theme = project.get("theme") or "새로운 화자의 독창적인 감정 이야기"
    title_seed = theme.split()[0] if theme else "그 밤"

    concept = {
        "new_song_concept": f"{mood} 정서를 {theme}로 풀어내는 {genre}",
        "genre": genre,
        "mood": [item.strip() for item in mood.split(",") if item.strip()] or [mood],
        "target_listener": project.get("target_listener") or "감정 서사와 후렴 훅을 선호하는 대중음악 청자",
        "one_sentence_pitch": f"{theme}를 새 화자와 새 이미지로 설계하는 독창적 {genre}",
    }
    emotion_curve = {
        "emotion_curve": [
            {"section": "Intro", "emotion": "정서 제시", "energy": 1},
            {"section": "Verse 1", "emotion": "상황 설명", "energy": 2},
            {"section": "Pre-Chorus", "emotion": "흔들림", "energy": 5},
            {"section": "Chorus", "emotion": "핵심 감정 고백", "energy": 8},
            {"section": "Bridge", "emotion": "새 관점", "energy": 4},
            {"section": "Final Chorus", "emotion": "확장과 정리", "energy": 10},
        ]
    }
    structure_plan = {
        "structure": [
            "Intro 4 bars",
            "Verse 1 8 bars",
            "Pre-Chorus 4 bars",
            "Chorus 8 bars",
            "Verse 2 8 bars",
            "Pre-Chorus 4 bars",
            "Chorus 8 bars",
            "Bridge 4 bars",
            "Final Chorus 8 bars",
            "Outro 4 bars",
        ],
        "reason": "레퍼런스의 에너지 상승 원리를 일반화해 벌스 절제, 후렴 집중, 마지막 후렴 확장으로 설계합니다.",
    }
    lyrics_plan = {
        "title_candidates": [f"{title_seed}의 밤", f"아직 남은 {title_seed}", f"{title_seed} 끝에서"],
        "lyric_speaker": "상황을 돌아보며 새 결심을 만드는 1인칭 화자",
        "core_sentence": f"나는 아직 {title_seed} 끝에서 나를 찾고 있어",
        "verse_1_plan": "현재 장면을 통해 감정을 직접 설명하기보다 이미지로 보여준다.",
        "pre_chorus_plan": "괜찮은 척하던 감정이 흔들리는 순간을 만든다.",
        "chorus_plan": "제목과 연결되는 새 문장을 반복해 기억성을 만든다.",
        "bridge_plan": "상대나 과거가 아니라 화자 자신의 선택을 가장 솔직하게 말한다.",
        "imagery": ["밤", "창문", "불빛", "빈 거리", "남은 온기"],
        "avoid_cliche": ["돌아와줘", "죽을 만큼 아파", "너 없인 안돼"],
    }
    harmony_plan = {
        "key": key,
        "bpm": bpm,
        "verse_progression_options": ["I - V - vi - IV", "vi - IV - I - V", "I - iii - IV - V"],
        "pre_chorus_progression_options": ["ii - V - iii - vi", "IV - V - iii - vi"],
        "chorus_progression_options": ["IV - V - iii - vi", "I - V - vi - IV", "vi - IV - I - V"],
        "recommended_progression": {"verse": "I - V - vi - IV", "pre_chorus": "ii - V - iii - vi", "chorus": "IV - V - iii - vi"},
        "reason": "후렴을 바로 해결하지 않고 열어두면 그리움과 여운이 유지됩니다. 이는 범용 화성 원리이며 특정 곡 복제가 아닙니다.",
    }
    melody_plan = {
        "verse_melody_direction": "낮은 음역에서 말하듯 시작하고 순차 진행을 중심으로 구성한다.",
        "pre_chorus_melody_direction": "음역을 조금씩 올려 후렴 전 긴장감을 만든다.",
        "chorus_melody_direction": "첫 두 마디는 짧은 반복 모티프로 기억성을 만들고 후반부에서 최고음에 도달한다.",
        "hook_shape": "짧은 상승 후 긴 하행",
        "peak_note_position": "chorus second half",
        "melody_rule": "처음부터 최고음을 쓰지 말고, 후렴 후반부에서 감정적 보상처럼 사용한다.",
    }
    hook_plan = {
        "hook_type": "lyric + melody hook",
        "hook_location": "chorus first two bars",
        "hook_length": "2 bars",
        "lyric_hook": lyrics_plan["core_sentence"],
        "melody_hook_direction": "같은 리듬을 두 번 반복하고 두 번째 반복에서 음을 한 단계 올린다.",
        "title_connection": "title phrase appears as newly written chorus hook",
        "repeat_strategy": "후렴마다 같은 의미를 반복하되 마지막 후렴에서 애드리브와 하모니로 확장한다.",
    }
    arrangement_plan = {
        "intro": "solo piano or signature texture with soft pad",
        "verse_1": "main instrument only, low density",
        "pre_chorus": "add low strings or subtle riser",
        "chorus": "add drums, bass, wide harmony layers",
        "verse_2": "keep light percussion and bass movement",
        "bridge": "drop drums and return to intimate texture",
        "final_chorus": "full drums, backing vocals, adlibs, high strings or synth lift",
        "outro": "resolve with reduced arrangement and long reverb",
    }
    vocal_plan = {
        "verse_vocal": project.get("vocal_style") or "가까이 말하듯, 숨소리가 느껴지는 톤",
        "pre_chorus_vocal": "점점 힘을 더하며 감정 상승",
        "chorus_vocal": "넓은 발성, 긴 음가, 감정적 고조",
        "double_tracking": "chorus only",
        "harmony": "final chorus second half",
        "adlib": "final chorus ending",
        "effects": ["plate reverb", "slap delay", "long delay throw"],
    }
    mixing_plan = {
        "mixing_direction": "보컬 중심의 넓은 대중음악 믹스",
        "vocal_position": "front and center",
        "low_end": "controlled and warm",
        "reverb": "medium-long plate reverb",
        "mastering": "streaming-friendly loudness, not overly compressed",
    }
    final_guide = (
        f"이번 신곡은 약 {bpm}BPM의 {genre}로 설계합니다. 핵심 정서는 {mood}이며, "
        f"주제는 '{theme}'입니다. Verse에서는 낮은 음역과 말하듯 흐르는 리듬을 사용하고, "
        "Chorus에서는 제목과 연결되는 새 문장을 반복해 기억성을 만듭니다. 코드와 편곡은 레퍼런스의 원리를 일반화한 것이며, "
        "기존 곡의 멜로디·가사·리프를 직접 차용하지 않습니다."
    )
    return {
        "concept": concept,
        "emotion_curve": emotion_curve,
        "structure_plan": structure_plan,
        "lyrics_plan": lyrics_plan,
        "harmony_plan": harmony_plan,
        "melody_plan": melody_plan,
        "hook_plan": hook_plan,
        "rhythm_plan": {"bpm": bpm, "meter": "4/4", "groove": "vocal-led pop groove", "final_chorus_rhythm_lift": "open hi-hat and cymbal swell"},
        "arrangement_plan": arrangement_plan,
        "vocal_plan": vocal_plan,
        "mixing_plan": mixing_plan,
        "final_production_guide": final_guide,
        "anti_copy_notice": "기존 곡의 공식을 그대로 복제하지 않고, 여러 곡에서 관찰된 창작 원리를 일반화해 새 곡으로 설계합니다.",
        "pattern_inputs": [pattern["description"] for pattern in patterns[:5]],
    }


def most_common(values: list[str | None]) -> str | None:
    counts: dict[str, int] = {}
    for value in values:
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return sorted(counts.items(), key=lambda item: item[1], reverse=True)[0][0] if counts else None


def infer_common_mood(analyses: list[dict[str, Any]]) -> str | None:
    moods: list[str] = []
    for analysis in analyses:
        moods.extend(analysis.get("concept", {}).get("mood", []))
    return most_common(moods)


def infer_target_bpm(bpm_range: str | None, songs: list[dict[str, Any]]) -> int:
    if bpm_range:
        numbers = [int(token) for token in bpm_range.replace("-", " ").split() if token.isdigit()]
        if numbers:
            return round(sum(numbers) / len(numbers))
    bpms = [float(song["bpm"]) for song in songs if song.get("bpm") is not None]
    return round(mean(bpms)) if bpms else 72
