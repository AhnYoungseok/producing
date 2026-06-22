from __future__ import annotations

from typing import Any


PRODUCER_SECTION_ORDER = [
    "production_concept",
    "structure_energy",
    "harmony_design",
    "melody_hook",
    "lyrics_storytelling",
    "rhythm_groove",
    "arrangement_layering",
    "vocal_production",
    "sound_mixing",
    "hit_points",
    "creative_application",
    "data_confidence",
]


PRODUCER_SECTION_TITLES = {
    "production_concept": "1. 프로덕션 컨셉",
    "structure_energy": "2. 곡 구조와 에너지 설계",
    "harmony_design": "3. 코드 진행과 화성",
    "melody_hook": "4. 멜로디와 후크",
    "lyrics_storytelling": "5. 가사와 스토리텔링",
    "rhythm_groove": "6. 리듬과 그루브",
    "arrangement_layering": "7. 편곡과 레이어링",
    "vocal_production": "8. 보컬 프로덕션",
    "sound_mixing": "9. 사운드 디자인과 믹싱",
    "hit_points": "10. 히트 포인트",
    "creative_application": "11. 내 곡에 적용할 원리",
    "data_confidence": "12. 데이터 신뢰도",
}


def generate_producer_sections(
    sections: dict[str, Any],
    metadata: dict[str, Any],
    audio_features: dict[str, Any],
    research_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = _build_context(sections, metadata, audio_features, research_profile)
    producer_sections = {
        "production_concept": _production_concept(context),
        "structure_energy": _structure_energy(context),
        "harmony_design": _harmony_design(context),
        "melody_hook": _melody_hook(context),
        "lyrics_storytelling": _lyrics_storytelling(context),
        "rhythm_groove": _rhythm_groove(context),
        "arrangement_layering": _arrangement_layering(context),
        "vocal_production": _vocal_production(context),
        "sound_mixing": _sound_mixing(context),
        "hit_points": _hit_points(context),
        "creative_application": _creative_application(context),
        "data_confidence": _data_confidence(context),
    }
    return producer_sections


def generate_producer_summary(
    sections: dict[str, Any],
    metadata: dict[str, Any],
    audio_features: dict[str, Any],
    research_profile: dict[str, Any] | None = None,
) -> str:
    context = _build_context(sections, metadata, audio_features, research_profile)
    bpm_text = f"약 {context['bpm']:.1f}BPM" if context["bpm"] else "BPM 미확정"
    key_text = context["key"] or "Key 미확정"
    mood_text = _join(context["moods"], "정서 미확정")
    return (
        f"{context['artist']}의 '{context['title']}'은 {context['genre']} 맥락에서 {mood_text}를 중심으로 정리되는 레퍼런스입니다. "
        f"현재 확보된 데이터 기준으로 템포는 {bpm_text}, 조성은 {key_text}이며, 후크는 {context['hook_type']} 방향으로 읽을 수 있습니다. "
        "이 리포트는 관찰, 해석, 창작 적용 순서로 정리되며 원곡의 멜로디나 가사를 복제하지 않고 창작 원리를 일반화하는 데 목적이 있습니다."
    )


def _build_context(
    sections: dict[str, Any],
    metadata: dict[str, Any],
    audio_features: dict[str, Any],
    research_profile: dict[str, Any] | None,
) -> dict[str, Any]:
    concept = sections.get("concept", {})
    lyrics = sections.get("lyrics", {})
    structure = sections.get("structure", {})
    harmony = sections.get("harmony", {})
    melody = sections.get("melody", {})
    hook = sections.get("hook", {})
    rhythm = sections.get("rhythm", {})
    arrangement = sections.get("arrangement", {})
    vocal = sections.get("vocal", {})
    mixing = sections.get("mixing", {})
    hit_factor = sections.get("hit_factor", {})
    takeaway = sections.get("takeaway", {})
    features = (research_profile or {}).get("musical_features", {})

    bpm = _to_float(audio_features.get("bpm") or rhythm.get("bpm") or _confidence_value(features.get("bpm")))
    title = metadata.get("title") or (research_profile or {}).get("identification", {}).get("title", {}).get("value") or "Untitled Reference"
    artist = metadata.get("artist") or (research_profile or {}).get("identification", {}).get("artist", {}).get("value") or "Unknown Artist"
    genre = metadata.get("genre") or concept.get("genre") or (research_profile or {}).get("identification", {}).get("genre", {}).get("value") or "장르 미확정"
    moods = _as_list(concept.get("mood")) or _as_list(_confidence_value(features.get("mood_tags")))
    structure_list = _as_list(structure.get("structure")) or ["Intro", "Verse", "Chorus", "Final Chorus"]
    key = harmony.get("key") or audio_features.get("estimated_key") or _confidence_value(features.get("key")) or "Unknown"
    hook_type = hook.get("primary_hook_type") or hook.get("hook_type") or _confidence_value(features.get("hook_type")) or "lyric + melody hook"

    return {
        "metadata": metadata,
        "research_profile": research_profile,
        "audio_features": audio_features,
        "concept": concept,
        "lyrics": lyrics,
        "structure": structure,
        "harmony": harmony,
        "melody": melody,
        "hook": hook,
        "rhythm": rhythm,
        "arrangement": arrangement,
        "vocal": vocal,
        "mixing": mixing,
        "hit_factor": hit_factor,
        "takeaway": takeaway,
        "features": features,
        "title": title,
        "artist": artist,
        "genre": genre,
        "moods": moods,
        "bpm": bpm,
        "key": key,
        "hook_type": hook_type,
        "structure_list": structure_list,
        "has_uploaded_audio": bool(metadata.get("file_name")) or audio_features.get("analysis_source") != "youtube_link_research_profile_no_youtube_audio",
    }


def _production_concept(context: dict[str, Any]) -> dict[str, Any]:
    concept = context["concept"]
    moods = _join(context["moods"], "정서 미확정")
    genre = context["genre"]
    return _section(
        "production_concept",
        observation=(
            f"이 레퍼런스는 {genre} 정체성을 바탕으로 {moods}를 전면에 두는 곡으로 정리됩니다. "
            f"핵심 컨셉은 {concept.get('concept') or concept.get('one_sentence_concept') or '메타데이터와 사용자 입력을 바탕으로 추정 중'}입니다."
        ),
        interpretation=(
            "프로듀서 관점에서는 장르 이름보다 감정이 어떤 방식으로 누적되는지가 중요합니다. "
            "초반에 정보를 적게 주고 후렴과 마지막 후렴에서 정서 밀도를 키우는 구조라면 대중적인 카타르시스를 만들기 쉽습니다."
        ),
        creative_application=(
            "새 곡에서는 같은 이미지를 복제하지 말고, 타깃 청자와 감정 키워드를 먼저 정한 뒤 사운드 이미지를 새로 설계하세요. "
            "컨셉 문장을 한 줄로 고정하면 코드, 가사, 편곡 선택이 흔들리지 않습니다."
        ),
        data_points={
            "곡의 핵심 컨셉": concept.get("concept") or concept.get("one_sentence_concept"),
            "장르 정체성": genre,
            "타깃 청자": concept.get("target_listener"),
            "감정 키워드": context["moods"],
            "사운드 이미지": concept.get("era_sound") or context["arrangement"].get("space_design"),
            "아티스트 이미지와의 연결": concept.get("artist_image_relation"),
            "상업적 포지셔닝": _commercial_position(context),
        },
    )


def _structure_energy(context: dict[str, Any]) -> dict[str, Any]:
    structure = context["structure"]
    structure_text = " - ".join(str(item) for item in context["structure_list"])
    first_chorus = structure.get("first_chorus_time")
    return _section(
        "structure_energy",
        observation=(
            f"현재 구조는 {structure_text} 흐름으로 정리됩니다. "
            f"첫 후렴 시점은 {first_chorus}초로 기록되어 있습니다." if first_chorus is not None else f"현재 구조는 {structure_text} 흐름으로 추정되며, 첫 후렴 시점은 아직 확정되지 않았습니다."
        ),
        interpretation=(
            "히트곡 연구에서는 후렴이 너무 늦게 나오지 않는지, 1절에서 청자를 붙잡는 장치가 있는지가 핵심입니다. "
            "마지막 후렴이 이전 후렴과 같은 밀도라면 반복 피로가 생기기 쉽고, 보컬/드럼/하모니/스트링 중 하나는 확장되어야 합니다."
        ),
        creative_application=(
            "새 곡을 설계할 때 첫 후렴 진입 시간을 의도적으로 정하세요. "
            "느린 발라드라면 1절의 가사 흡입력, 업템포 팝이라면 첫 30초의 리듬 또는 사운드 후크가 중요합니다."
        ),
        data_points={
            "Intro 길이": structure.get("intro_length") or "미확정",
            "Verse 역할": structure.get("verse_role") or "상황과 정서를 제시하는 구간",
            "Pre-Chorus 유무": "Pre-Chorus" in structure_text,
            "Chorus 등장 시점": first_chorus,
            "Bridge 역할": structure.get("bridge_role") or "반복을 잠시 끊고 마지막 후렴을 준비하는 구간",
            "Final Chorus 확장 방식": structure.get("final_chorus_expansion") or context["arrangement"].get("final_chorus_lift"),
            "파트별 에너지 변화": structure.get("energy_curve") or "MVP 추정 필요",
            "반복과 변주의 비율": structure.get("variation_ratio") or "반복 중심, 마지막 후렴 변주 권장",
        },
    )


def _harmony_design(context: dict[str, Any]) -> dict[str, Any]:
    harmony = context["harmony"]
    chorus_progression = harmony.get("chorus_progression") or "코드 진행 미입력"
    return _section(
        "harmony_design",
        observation=(
            f"조성은 {context['key']}로 정리되고, 후렴 코드 진행은 {chorus_progression}로 기록되어 있습니다."
        ),
        interpretation=(
            "대중적인 화성은 완전히 새로워서가 아니라 익숙한 해결감과 약간의 미해결 긴장을 균형 있게 배치할 때 힘이 생깁니다. "
            "후렴을 I로 바로 시작하면 안정적이고, IV나 vi 계열로 열면 감정이 더 떠 있는 느낌을 만들 수 있습니다."
        ),
        creative_application=(
            "새 곡에서는 코드 진행을 그대로 가져오기보다 '어디서 열고 어디서 닫는지'를 참고하세요. "
            "후렴 직전에는 V, ii-V, IV-V 같은 긴장 장치를 쓰고, 후렴 첫 마디에서 해결 또는 유보 중 하나를 명확히 선택하는 것이 좋습니다."
        ),
        data_points={
            "Key": context["key"],
            "Verse 코드 진행": harmony.get("verse_progression"),
            "Pre-Chorus 코드 진행": harmony.get("pre_chorus_progression"),
            "Chorus 코드 진행": chorus_progression,
            "Bridge 코드 진행": harmony.get("bridge_progression"),
            "차용화음": harmony.get("borrowed_chords") or "미확정",
            "세컨더리 도미넌트": harmony.get("secondary_dominants") or "미확정",
            "전조 여부": harmony.get("has_modulation"),
            "감정을 여는 코드": harmony.get("opening_emotion_chord") or "IV, vi 계열 후보",
            "감정을 닫는 코드": harmony.get("closing_emotion_chord") or "I 또는 V-I 해결 후보",
            "후렴 진입 전 긴장 코드": harmony.get("tension_code_role"),
        },
    )


def _melody_hook(context: dict[str, Any]) -> dict[str, Any]:
    melody = context["melody"]
    hook = context["hook"]
    hook_type = context["hook_type"]
    return _section(
        "melody_hook",
        observation=(
            f"후크 유형은 {hook_type}로 정리됩니다. "
            f"멜로디 정보는 {melody.get('analysis_note') or '사용자 제공 악보나 권리 보유 오디오가 있을 때 더 정확해집니다.'}"
        ),
        interpretation=(
            "청자가 기억하는 지점은 보통 복잡한 전체 멜로디가 아니라 후렴 첫 두 마디의 리듬, 음형, 제목 연결입니다. "
            "후크가 너무 길거나 음정 이동이 과하면 따라 부르기 어렵고, 너무 평평하면 각인이 약해집니다."
        ),
        creative_application=(
            "새 곡에서는 후렴 첫 두 마디에 짧은 반복 모티브를 만들고, 두 번째 반복에서 음역이나 리듬을 살짝 바꾸세요. "
            "원곡의 멜로디 라인은 절대 복제하지 말고 후크의 위치, 길이, 반복 전략만 참고합니다."
        ),
        data_points={
            "후렴 첫 음": melody.get("chorus_first_note") or "미확정",
            "후렴 최고음 위치": melody.get("chorus_peak_position"),
            "멜로디 음역": melody.get("melody_range"),
            "반복 모티브": melody.get("motif_type"),
            "순차/도약 진행": melody.get("interval_style"),
            "가사 강세와 멜로디 강세": melody.get("lyric_melody_stress") or "미확정",
            "기억되는 2마디 구간": hook.get("hook_location") or "후렴 첫 두 마디 후보",
            "후크 유형": hook_type,
            "후크 반복 방식": hook.get("repeat_strategy") or hook.get("hook_repeat_count"),
            "제목과 후크의 연결": hook.get("title_hook_connection"),
        },
    )


def _lyrics_storytelling(context: dict[str, Any]) -> dict[str, Any]:
    lyrics = context["lyrics"]
    theme = lyrics.get("lyric_theme") or _confidence_value(context["features"].get("lyric_theme")) or "가사 테마 미확정"
    return _section(
        "lyrics_storytelling",
        observation=(
            f"가사 테마는 {theme}로 정리됩니다. "
            f"제목 사용 방식은 {lyrics.get('title_usage') or '미확정'}입니다."
        ),
        interpretation=(
            "좋은 히트곡 가사는 설명을 많이 해서가 아니라 청자가 자기 이야기처럼 가져갈 수 있는 문장으로 남습니다. "
            "Verse는 상황을 만들고, Pre-Chorus는 감정을 흔들며, Chorus는 제목과 연결되는 핵심 문장을 고정하는 역할을 해야 합니다."
        ),
        creative_application=(
            "새 곡에서는 후렴 첫 줄에 제목 또는 제목과 같은 기능을 하는 짧은 문장을 배치하세요. "
            "원곡의 표현은 그대로 차용하지 말고, 화자/상황/감정 곡선만 새 이야기로 변형해야 합니다."
        ),
        data_points={
            "화자": lyrics.get("lyric_point_of_view"),
            "대상": lyrics.get("addressee") or "미확정",
            "상황": lyrics.get("situation") or "사용자 가사 입력 시 분석 가능",
            "핵심 감정": theme,
            "가사 시점": lyrics.get("lyric_point_of_view"),
            "Verse 역할": lyrics.get("verse_role"),
            "Pre-Chorus 역할": lyrics.get("pre_chorus_role"),
            "Chorus 역할": lyrics.get("chorus_role"),
            "Bridge 역할": lyrics.get("bridge_role") or "가장 솔직한 고백 또는 시점 전환 후보",
            "제목 사용 위치": lyrics.get("title_usage"),
            "반복 문장": lyrics.get("repeated_key_phrases"),
            "은유와 직접 표현의 비율": lyrics.get("metaphor_level"),
            "감정 변화": lyrics.get("emotion_curve"),
        },
    )


def _rhythm_groove(context: dict[str, Any]) -> dict[str, Any]:
    rhythm = context["rhythm"]
    bpm = context["bpm"]
    bpm_text = f"{bpm:.1f}BPM" if bpm else "BPM 미확정"
    return _section(
        "rhythm_groove",
        observation=(
            f"템포는 {bpm_text}, 그루브는 {rhythm.get('groove_type') or '미확정'}로 정리됩니다."
        ),
        interpretation=(
            "리듬 설계는 빠르기보다 파트 간 호흡 차이가 중요합니다. "
            "Verse에서 말하듯 촘촘하게 움직이고 Chorus에서 긴 음가로 열리면, 느린 곡도 지루하지 않게 감정이 확장됩니다."
        ),
        creative_application=(
            "새 곡에서는 드럼을 복잡하게 만들기 전에 보컬 리듬의 말맛을 먼저 정하세요. "
            "후렴에서는 킥/스네어/하이햇 중 하나를 명확히 열어 Verse와 대비를 만드는 것이 좋습니다."
        ),
        data_points={
            "BPM": bpm,
            "박자": rhythm.get("meter") or "4/4 후보",
            "드럼 진입 시점": rhythm.get("drum_entry") or "첫 후렴 또는 2절 후보",
            "킥 패턴": rhythm.get("kick_pattern") or "미확정",
            "스네어 위치": rhythm.get("snare_position") or "2, 4박 후보",
            "하이햇 밀도": rhythm.get("hihat_density") or rhythm.get("rhythm_density"),
            "보컬 리듬": rhythm.get("vocal_rhythm") or "가사 입력 기반 추가 분석 필요",
            "싱코페이션": rhythm.get("syncopation") or "미확정",
            "Verse와 Chorus의 리듬 대비": f"{rhythm.get('verse_rhythm_density')} -> {rhythm.get('chorus_rhythm_density')}",
            "느린 곡의 지루함 방지 장치": "보컬 호흡, 코드 전환, 레이어 증가",
        },
    )


def _arrangement_layering(context: dict[str, Any]) -> dict[str, Any]:
    arrangement = context["arrangement"]
    return _section(
        "arrangement_layering",
        observation=(
            f"편곡 빌드는 {arrangement.get('arrangement_build') or '미확정'}로 정리됩니다. "
            f"후렴 편곡은 {arrangement.get('chorus_arrangement') or '사용자 메모 또는 권리 보유 오디오로 확인 필요'}입니다."
        ),
        interpretation=(
            "프로듀서 관점에서는 악기가 얼마나 많은가보다 언제 들어오고 언제 빠지는지가 더 중요합니다. "
            "초반부터 모든 악기를 쓰면 후렴이 커질 공간이 사라지고, 보컬 메시지를 방해할 수 있습니다."
        ),
        creative_application=(
            "새 곡에서는 Intro와 Verse를 비워 두고, Pre-Chorus에서 긴장 레이어를 추가한 뒤 Chorus에서 리듬과 저역을 여는 방식을 우선 실험하세요. "
            "특정 리프나 사운드 시그니처는 복제하지 말고 레이어링 원리만 가져옵니다."
        ),
        data_points={
            "Intro 악기": arrangement.get("intro_instruments"),
            "Verse 악기": arrangement.get("verse_instruments"),
            "Pre-Chorus 악기": arrangement.get("pre_chorus_instruments"),
            "Chorus 악기": arrangement.get("chorus_arrangement"),
            "Bridge 악기": arrangement.get("bridge_arrangement"),
            "Final Chorus 악기": arrangement.get("final_chorus_lift"),
            "악기 추가 시점": arrangement.get("instrument_add_points") or "Pre-Chorus, Chorus, Final Chorus 후보",
            "악기 제거 시점": arrangement.get("instrument_drop_points") or "Bridge 또는 후렴 직전 드롭아웃 후보",
            "빌드업 장치": arrangement.get("build_up_devices") or "riser, cymbal, pad, harmony layer 후보",
            "드롭/감정 폭발 지점": arrangement.get("drop_or_peak") or "Chorus 또는 Final Chorus 후보",
            "스트링 사용": _contains_instruments(arrangement, ["strings", "string", "스트링"]),
            "피아노 사용": _contains_instruments(arrangement, ["piano", "피아노"]),
            "기타 사용": _contains_instruments(arrangement, ["guitar", "기타"]),
            "신스 패드 사용": _contains_instruments(arrangement, ["synth", "pad", "신스", "패드"]),
            "FX 사용": arrangement.get("fx_usage") or "미확정",
            "공간감": arrangement.get("space_design"),
        },
    )


def _vocal_production(context: dict[str, Any]) -> dict[str, Any]:
    vocal = context["vocal"]
    return _section(
        "vocal_production",
        observation=(
            f"보컬 톤은 {vocal.get('vocal_tone') or '미확정'}로 정리되고, 후렴 전달 방식은 {vocal.get('chorus_delivery') or '미확정'}입니다."
        ),
        interpretation=(
            "보컬 프로덕션의 핵심은 1절과 후렴의 거리감 차이입니다. "
            "Verse가 가까이 말하는 느낌이고 Chorus가 넓게 열리면, 청자는 이야기에서 감정 폭발로 자연스럽게 이동합니다."
        ),
        creative_application=(
            "새 곡에서는 Verse 보컬을 건조하고 가깝게, Chorus 보컬을 더블링/하모니/리버브로 넓히는 대비를 설계하세요. "
            "원곡 가창의 애드리브나 발음 습관을 그대로 따라 하지 않는 것이 중요합니다."
        ),
        data_points={
            "보컬 톤": vocal.get("vocal_tone"),
            "호흡": vocal.get("breath_usage") or "미확정",
            "발음": vocal.get("diction") or "미확정",
            "감정 표현": vocal.get("emotional_delivery") or vocal.get("chorus_delivery"),
            "Verse 보컬 처리": vocal.get("verse_delivery"),
            "Chorus 보컬 처리": vocal.get("chorus_delivery"),
            "더블링": _contains_text(vocal.get("vocal_effects"), "doubling"),
            "하모니": vocal.get("harmony") or "Final Chorus 후보",
            "애드리브": vocal.get("adlib_usage") or vocal.get("adlib"),
            "코러스 보컬": vocal.get("backing_vocals") or "후렴/마지막 후렴 후보",
            "오토튠 느낌": vocal.get("autotune_feel") or "미확정",
            "리버브": _contains_text(vocal.get("vocal_effects"), "reverb"),
            "딜레이": _contains_text(vocal.get("vocal_effects"), "delay"),
            "보컬 위치": context["mixing"].get("vocal_position"),
        },
    )


def _sound_mixing(context: dict[str, Any]) -> dict[str, Any]:
    mixing = context["mixing"]
    audio = context["audio_features"]
    return _section(
        "sound_mixing",
        observation=(
            f"믹스는 보컬 위치 {mixing.get('vocal_position') or '미확정'}, 저역 밀도 {mixing.get('low_end_density') or '미확정'}, "
            f"마스터링 성향 {mixing.get('mastering_loudness_style') or '미확정'}로 정리됩니다."
        ),
        interpretation=(
            "상업 음원에서 보컬은 곡의 감정 중심입니다. 저역이 과하게 부풀면 보컬의 말맛과 코드 감정이 흐려지고, 공간계가 과하면 가사가 뒤로 밀릴 수 있습니다."
        ),
        creative_application=(
            "새 곡에서는 보컬을 전면에 세운 뒤 피아노/기타/신스/스트링을 좌우와 깊이로 분리하세요. "
            "음압을 올리는 것보다 스트리밍에서 피로하지 않은 선명도를 확보하는 것이 먼저입니다."
        ),
        data_points={
            "보컬 전면감": mixing.get("vocal_position"),
            "저역 밀도": mixing.get("low_end_density"),
            "중역 존재감": mixing.get("mid_presence") or "보컬 중심 확인 필요",
            "고역 밝기": audio.get("spectral_centroid_mean"),
            "스테레오 폭": mixing.get("stereo_width"),
            "리버브 양": mixing.get("reverb_amount"),
            "딜레이 사용": mixing.get("delay_usage") or "보컬 효과 정보 기반 확인 필요",
            "드럼 전면감": mixing.get("drum_presence") or "미확정",
            "악기 분리도": mixing.get("separation") or "미확정",
            "마스터링 음압": audio.get("loudness_estimate"),
            "스트리밍 친화성": mixing.get("radio_streaming_fit"),
            "라디오 친화성": mixing.get("radio_fit") or mixing.get("radio_streaming_fit"),
        },
    )


def _hit_points(context: dict[str, Any]) -> dict[str, Any]:
    hit_factor = context["hit_factor"]
    hook_type = context["hook_type"]
    return _section(
        "hit_points",
        observation=(
            f"가장 강한 대중성 요소는 {hit_factor.get('main_hit_factor') or hook_type}로 정리됩니다."
        ),
        interpretation=(
            "히트 포인트는 가사, 멜로디, 리듬 중 하나가 혼자 강해서 생기기보다 제목 기억성, 후렴 진입 타이밍, 따라 부르기 쉬운 2마디가 동시에 맞물릴 때 강해집니다."
        ),
        creative_application=(
            "새 곡에서는 첫 30초 안에 곡의 정체성을 보여주고, 후렴 첫 줄에 제목과 연결되는 새 문장을 배치하세요. "
            "SNS/숏폼을 의식한다면 후렴 전 드롭아웃, 한 박자 정지, 짧은 콜앤리스폰스 같은 장치를 새롭게 설계할 수 있습니다."
        ),
        data_points={
            "가장 강한 대중성 요소": hit_factor.get("main_hit_factor"),
            "따라 부르기 쉬운 부분": context["hook"].get("hook_location") or "후렴 첫 두 마디 후보",
            "감정 이입 포인트": hit_factor.get("emotional_identification"),
            "첫 30초 흡입력": hit_factor.get("first_30_seconds_impact"),
            "후렴 진입 타이밍": context["structure"].get("first_chorus_time"),
            "제목 기억성": context["hook"].get("title_hook_connection") or context["lyrics"].get("title_usage"),
            "SNS/숏폼 활용 가능성": hit_factor.get("short_form_potential") or "후크가 짧고 반복적이면 강화 가능",
            "라이브 무대 포인트": hit_factor.get("live_moment") or "Final Chorus 애드리브/떼창 후보",
            "반복 청취 요소": hit_factor.get("replay_factor"),
        },
    )


def _creative_application(context: dict[str, Any]) -> dict[str, Any]:
    takeaway = context["takeaway"]
    principles = _as_list(takeaway.get("transferable_principles"))
    avoid = _as_list(takeaway.get("avoid_copying"))
    return _section(
        "creative_application",
        observation=(
            f"이 곡에서 추출할 수 있는 핵심 원리는 {_join(principles[:2], '초반 절제, 후렴 집중, 마지막 확장')}입니다."
        ),
        interpretation=(
            "레퍼런스 분석의 목적은 공식을 베끼는 것이 아니라 결정의 이유를 배우는 것입니다. "
            "어떤 파트에서 비우고, 어디서 제목을 각인시키고, 마지막 후렴에서 무엇을 확장하는지에 집중해야 합니다."
        ),
        creative_application=(
            "내 곡에는 같은 멜로디나 가사를 쓰지 말고, 구조적 원리를 새 컨셉에 맞게 바꾸어 적용하세요. "
            "추천 전략은 Verse에서 정보량을 줄이고, Chorus 첫 두 마디에 새 제목형 후크를 배치한 뒤, Final Chorus에서 보컬/하모니/리듬 중 하나를 확장하는 것입니다."
        ),
        data_points={
            "이 곡에서 배울 수 있는 점": principles,
            "내 곡에 적용 가능한 원리": principles,
            "그대로 따라 하면 안 되는 요소": avoid,
            "변형해서 사용할 수 있는 아이디어": takeaway.get("creative_use") or "후크 위치, 에너지 곡선, 레이어 확장 방식",
            "추천 작곡 전략": "컨셉 한 줄 -> 감정선 -> 후렴 첫 두 마디 -> 코드 긴장/해소 -> 마지막 후렴 확장 순서로 설계",
        },
    )


def _data_confidence(context: dict[str, Any]) -> dict[str, Any]:
    profile = context["research_profile"] or {}
    features = profile.get("musical_features", {})
    confidence_items = {
        "BPM": features.get("bpm"),
        "Key": features.get("key"),
        "Mood Tags": features.get("mood_tags"),
        "Lyric Theme": features.get("lyric_theme"),
        "Hook Type": features.get("hook_type"),
        "Structure Notes": features.get("structure_notes"),
        "Arrangement Notes": features.get("arrangement_notes"),
        "Hit Factors": features.get("hit_factors"),
    }
    source_text = (
        "이 분석에는 사용자가 업로드한 권리 보유 오디오의 신호 분석이 포함됩니다."
        if context["has_uploaded_audio"]
        else "이 분석은 YouTube 오디오를 사용하지 않는 링크 기반 리서치 프로필입니다."
    )
    return _section(
        "data_confidence",
        observation=source_text,
        interpretation=(
            "high는 신뢰 가능한 구조화 API 또는 실제 업로드 오디오 분석, medium은 여러 출처나 사용자 입력 기반 추론, low는 제한된 메타데이터나 메모 기반 추정입니다."
        ),
        creative_application=(
            "작곡에 바로 반영하기 전, low confidence 항목은 직접 청취 메모, 합법적 악보, 사용자가 보유한 오디오 분석, 코드 입력으로 보강하세요."
        ),
        data_points={
            "YouTube 사용 범위": "메타데이터와 참고 링크만 사용",
            "금지된 처리": ["YouTube 오디오 다운로드", "오디오 추출", "오디오 분리", "스트림 캡처", "yt-dlp/youtube-dl 사용"],
            "실제 오디오 분석 출처": "사용자 업로드 파일만" if context["has_uploaded_audio"] else "없음",
            "Feature Confidence": {label: value for label, value in confidence_items.items() if value},
        },
    )


def _section(
    section_id: str,
    observation: str,
    interpretation: str,
    creative_application: str,
    data_points: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": section_id,
        "title": PRODUCER_SECTION_TITLES[section_id],
        "observation": observation,
        "interpretation": interpretation,
        "creative_application": creative_application,
        "data_points": data_points,
    }


def _commercial_position(context: dict[str, Any]) -> str:
    bpm = context["bpm"]
    genre = context["genre"]
    if bpm and bpm < 85:
        return f"{genre} 안에서 보컬 감정선과 후렴 카타르시스를 앞세우는 포지션"
    if bpm and bpm >= 120:
        return f"{genre} 안에서 리듬, 후크, 반복 청취성을 앞세우는 포지션"
    return f"{genre} 안에서 감정 전달과 대중적 후크의 균형을 노리는 포지션"


def _contains_instruments(arrangement: dict[str, Any], needles: list[str]) -> bool:
    values = []
    for key in ["main_instruments", "intro_instruments", "verse_instruments", "pre_chorus_instruments", "chorus_arrangement", "final_chorus_lift"]:
        values.extend(_as_list(arrangement.get(key)))
    text = " ".join(str(value).lower() for value in values)
    return any(needle.lower() in text for needle in needles)


def _contains_text(value: Any, needle: str) -> bool:
    return needle.lower() in " ".join(str(item).lower() for item in _as_list(value))


def _confidence_value(field: Any) -> Any:
    if isinstance(field, dict) and "value" in field:
        return field.get("value")
    return field


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _join(values: list[Any], fallback: str) -> str:
    normalized = [str(value) for value in values if value not in (None, "", [])]
    return ", ".join(normalized) if normalized else fallback


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
