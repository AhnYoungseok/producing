from __future__ import annotations

from typing import Any


COMPOSER_STAGES: list[dict[str, Any]] = [
    {"number": 1, "key": "direction", "title": "만들고 싶은 곡의 방향 묻기"},
    {"number": 2, "key": "genre_mood", "title": "장르와 감정 정하기"},
    {"number": 3, "key": "reference_recommendation", "title": "참고할 히트곡 추천하기"},
    {"number": 4, "key": "reference_patterns", "title": "추천곡들의 공통 특징 정리하기"},
    {"number": 5, "key": "concept", "title": "새 곡 컨셉 제안하기"},
    {"number": 6, "key": "lyrics_titles", "title": "가사 주제와 제목 후보 제안하기"},
    {"number": 7, "key": "emotion_curve", "title": "감정선 설계하기"},
    {"number": 8, "key": "structure", "title": "곡 구조 설계하기"},
    {"number": 9, "key": "harmony", "title": "코드 진행 후보 제안하기"},
    {"number": 10, "key": "melody", "title": "멜로디 방향 제안하기"},
    {"number": 11, "key": "hook", "title": "후크 설계하기"},
    {"number": 12, "key": "rhythm", "title": "리듬과 그루브 설계하기"},
    {"number": 13, "key": "arrangement", "title": "편곡 방향 제안하기"},
    {"number": 14, "key": "vocal", "title": "보컬 프로덕션 제안하기"},
    {"number": 15, "key": "mixing", "title": "믹싱 방향 제안하기"},
    {"number": 16, "key": "final_guide", "title": "최종 작곡 설계도 정리하기"},
]


def compose_assistant_turn(
    project: dict[str, Any],
    blueprint: dict[str, Any],
    recommendation_bundle: dict[str, Any],
) -> dict[str, Any]:
    """Create the next deterministic coaching prompt and option set."""
    stage_number = int(blueprint.get("current_stage") or 1)
    stage = get_stage(stage_number)
    options = _options_for_stage(stage_number, project, blueprint, recommendation_bundle)
    return {
        "stage": stage_number,
        "stage_key": stage["key"],
        "stage_title": stage["title"],
        "assistant_message": _stage_message(stage_number, project, blueprint, recommendation_bundle),
        "options": options,
        "recommendations": recommendation_bundle if stage_number in {3, 4} else None,
    }


def get_stage(stage_number: int) -> dict[str, Any]:
    normalized = max(1, min(stage_number, len(COMPOSER_STAGES)))
    return COMPOSER_STAGES[normalized - 1]


def get_stage_title(stage_number: int) -> str:
    return get_stage(stage_number)["title"]


def _stage_message(
    stage_number: int,
    project: dict[str, Any],
    blueprint: dict[str, Any],
    recommendation_bundle: dict[str, Any],
) -> str:
    stage = get_stage(stage_number)
    genre = project.get("target_genre") or _read_nested(blueprint, "concept", "genre") or "아직 정하지 않은 장르"
    mood = project.get("target_mood") or _read_nested(blueprint, "concept", "mood") or "아직 정하지 않은 감정"
    if stage_number == 1:
        return (
            f"1단계입니다. '{project.get('title')}' 프로젝트가 어떤 결의 곡이 되면 좋을지 먼저 잡아볼게요. "
            "아래 세 방향 중 하나를 고르거나, 원하는 방향을 직접 적어 주세요."
        )
    if stage_number == 3:
        names = ", ".join(f"{item['artist']} - {item['title']}" for item in recommendation_bundle.get("recommendations", [])[:3])
        return (
            "3단계입니다. MVP에서는 외부 검색 대신 큐레이션된 mock reference data와 사용자가 저장한 분석곡을 바탕으로 추천합니다. "
            f"현재는 {names or '저장된 레퍼런스'} 흐름이 잘 맞습니다. 어떤 기준으로 레퍼런스 묶음을 잡을까요?"
        )
    if stage_number == 4:
        return (
            "4단계입니다. 추천곡들을 베끼는 대신 공통 원리를 추려 새 곡의 설계 규칙으로 바꾸겠습니다. "
            "가장 중요하게 가져갈 패턴을 고르세요."
        )
    if stage_number == 16:
        return (
            "마지막 단계입니다. 지금까지의 선택을 하나의 제작 가이드로 정리하겠습니다. "
            "최종 설계도의 톤을 고르면 실제 작곡 노트처럼 이어 붙이겠습니다."
        )
    return (
        f"{stage_number}단계, {stage['title']}입니다. 현재 방향은 {genre}, 핵심 정서는 {mood} 쪽입니다. "
        "세 가지 선택지 중 하나를 고르거나 직접 수정안을 입력하면 설계도에 반영하겠습니다."
    )


def _options_for_stage(
    stage_number: int,
    project: dict[str, Any],
    blueprint: dict[str, Any],
    recommendation_bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    option_map = {
        1: _direction_options,
        2: _genre_mood_options,
        3: _reference_options,
        4: _pattern_options,
        5: _concept_options,
        6: _lyrics_title_options,
        7: _emotion_options,
        8: _structure_options,
        9: _harmony_options,
        10: _melody_options,
        11: _hook_options,
        12: _rhythm_options,
        13: _arrangement_options,
        14: _vocal_options,
        15: _mixing_options,
        16: _final_options,
    }
    builder = option_map.get(stage_number, _direction_options)
    return builder(project, blueprint, recommendation_bundle)


def _direction_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _option(
            1,
            "A",
            "담담한 회상형 발라드",
            "김광석·아이유식으로 큰 폭발보다 가까운 말투와 장면 묘사를 중심에 둡니다.",
            {"concept": {"direction": "담담한 회상형 발라드", "one_sentence_pitch": "끝난 감정을 조용히 돌아보는 회상형 발라드"}},
        ),
        _option(
            1,
            "B",
            "감정 고조형 K-pop 발라드",
            "정승환식으로 벌스는 절제하고 후렴에서 보컬과 편곡을 크게 올립니다.",
            {"concept": {"direction": "감정 고조형 K-pop 발라드", "one_sentence_pitch": "절제에서 폭발로 상승하는 드라마틱 발라드"}},
        ),
        _option(
            1,
            "C",
            "세련된 팝 발라드",
            "태연·글로벌 팝 발라드처럼 선명한 후크와 넓은 사운드로 설계합니다.",
            {"concept": {"direction": "세련된 팝 발라드", "one_sentence_pitch": "모던한 사운드와 제목 후크가 중심인 팝 발라드"}},
        ),
    ]


def _genre_mood_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _option(2, "A", "K-pop Ballad / 그리움", "70~80BPM의 느린 템포에서 그리움과 고백을 키웁니다.", {"concept": {"genre": "K-pop Ballad", "mood": ["그리움", "회상", "고조"]}, "rhythm_groove": {"bpm_range": "70-80"}}),
        _option(2, "B", "Pop Ballad / 따뜻한 위로", "조금 더 보편적인 팝 발라드 문법으로 위로와 확장을 만듭니다.", {"concept": {"genre": "Pop Ballad", "mood": ["위로", "따뜻함", "확장"]}, "rhythm_groove": {"bpm_range": "68-78"}}),
        _option(2, "C", "Acoustic Ballad / 담담함", "어쿠스틱 악기와 가까운 보컬로 말하듯 감정을 전달합니다.", {"concept": {"genre": "Acoustic Ballad", "mood": ["담담함", "친밀함", "회상"]}, "rhythm_groove": {"bpm_range": "72-84"}}),
    ]


def _reference_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    references = recommendation_bundle.get("recommendations", [])
    return [
        _option(3, "A", "한국 발라드 중심", "K-pop 발라드의 보컬 고조, 후렴 문장, 마지막 후렴 확장을 중점 참고합니다.", {"reference_strategy": "한국 발라드 중심", "selected_reference_ids": [item["id"] for item in references if item.get("country") == "KR"][:5]}),
        _option(3, "B", "글로벌 팝 발라드 포함", "Adele, John Legend 계열의 단순한 피아노/보컬 중심 설계도 함께 참고합니다.", {"reference_strategy": "글로벌 팝 발라드 포함", "selected_reference_ids": [item["id"] for item in references][:5]}),
        _option(3, "C", "내 라이브러리 우선", "사용자가 직접 분석한 곡을 우선 기준으로 삼고 mock data는 보조 자료로 사용합니다.", {"reference_strategy": "내 라이브러리 우선", "selected_reference_ids": [item["id"] for item in references if str(item["id"]).startswith("song_")][:5]}),
    ]


def _pattern_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    patterns = recommendation_bundle.get("common_patterns", [])
    return [
        _option(4, "A", "초반 절제, 후렴 집중", "벌스에서 밀도를 낮추고 후렴에서 보컬과 악기 레이어를 확장합니다.", {"reference_patterns": patterns, "core_pattern": "초반 절제, 후렴 집중, 마지막 확장"}),
        _option(4, "B", "제목 연결 후크", "후렴 첫 두 마디에 제목과 연결되는 짧은 새 문장을 배치합니다.", {"reference_patterns": patterns, "core_pattern": "제목과 후렴 첫 문장의 강한 연결"}),
        _option(4, "C", "마지막 후렴 리프트", "마지막 후렴에서 하모니, 애드리브, 스트링 또는 신스 레이어를 추가합니다.", {"reference_patterns": patterns, "core_pattern": "마지막 후렴의 편곡·보컬 리프트"}),
    ]


def _concept_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    theme = project.get("theme") or "늦은 밤의 회상"
    return [
        _option(5, "A", "늦은 밤 회상", "혼자 남은 밤의 풍경을 통해 지나간 관계를 담담하게 돌아봅니다.", {"concept": {"new_song_concept": f"{theme}을 늦은 밤의 장면으로 풀어내는 발라드", "target_listener": project.get("target_listener") or "감성 발라드 청자"}}),
        _option(5, "B", "괜찮은 척하는 고백", "겉으로는 담담하지만 후렴에서 무너지는 감정선을 중심에 둡니다.", {"concept": {"new_song_concept": "괜찮은 척하던 화자가 후렴에서 진심을 인정하는 곡", "target_listener": project.get("target_listener") or "20-40대 팝 발라드 청자"}}),
        _option(5, "C", "위로와 재출발", "상실을 인정한 뒤 마지막 후렴에서 작게 앞으로 나아갑니다.", {"concept": {"new_song_concept": "상실 이후의 회복과 재출발을 그리는 팝 발라드", "target_listener": project.get("target_listener") or "넓은 대중 청자"}}),
    ]


def _lyrics_title_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _option(6, "A", "아직 그 밤에", "밤, 창문, 꺼진 불 이미지를 중심으로 제목과 후렴을 연결합니다.", {"title_candidates": ["아직 그 밤에", "불 꺼진 창가", "너를 놓은 뒤에"], "lyrics_direction": {"speaker": "이별을 받아들이려 하지만 아직 마음이 남아 있는 화자", "core_sentence": "아직도 나는 그 밤에 멈춰 있어", "imagery": ["밤", "창문", "꺼진 불", "남은 온기"]}}),
        _option(6, "B", "괜찮은 척", "담담한 일상 언어와 후렴의 직접 고백을 대비시킵니다.", {"title_candidates": ["괜찮은 척", "아무렇지 않은 말", "그 말 뒤에"], "lyrics_direction": {"speaker": "아무렇지 않은 척 말하지만 속으로 흔들리는 화자", "core_sentence": "괜찮은 척해도 아직 너야", "imagery": ["문자", "빈 방", "무심한 대답"]}}),
        _option(6, "C", "다시 켜지는 마음", "상실 뒤에 남는 작은 회복의 이미지를 사용합니다.", {"title_candidates": ["다시 켜지는 마음", "작은 불빛", "돌아오는 계절"], "lyrics_direction": {"speaker": "상실을 지나 새 계절을 받아들이는 화자", "core_sentence": "꺼진 줄 알았던 마음이 다시 켜져", "imagery": ["새벽", "불빛", "계절", "숨"]}}),
    ]


def _emotion_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _option(7, "A", "담담함에서 폭발로", "Intro 1, Verse 2, Pre 5, Chorus 8, Bridge 4, Final 10으로 크게 상승합니다.", {"emotion_curve": [{"section": "Intro", "emotion": "쓸쓸함", "energy": 1}, {"section": "Verse 1", "emotion": "담담한 회상", "energy": 2}, {"section": "Pre-Chorus", "emotion": "흔들림", "energy": 5}, {"section": "Chorus", "emotion": "그리움 고백", "energy": 8}, {"section": "Bridge", "emotion": "솔직한 인정", "energy": 4}, {"section": "Final Chorus", "emotion": "폭발과 정리", "energy": 10}]}),
        _option(7, "B", "처음부터 깊은 몰입", "첫 소절부터 감정을 열되, 후렴에서는 더 넓은 사운드로 확장합니다.", {"emotion_curve": [{"section": "Intro", "emotion": "깊은 몰입", "energy": 3}, {"section": "Verse 1", "emotion": "직접 고백", "energy": 4}, {"section": "Chorus", "emotion": "넓은 확장", "energy": 8}, {"section": "Final Chorus", "emotion": "가장 큰 고백", "energy": 10}]}),
        _option(7, "C", "절제된 회복", "감정을 과하게 폭발시키지 않고 마지막에 작은 희망으로 정리합니다.", {"emotion_curve": [{"section": "Intro", "emotion": "공백", "energy": 1}, {"section": "Verse", "emotion": "회상", "energy": 2}, {"section": "Chorus", "emotion": "인정", "energy": 6}, {"section": "Bridge", "emotion": "숨 고르기", "energy": 3}, {"section": "Final Chorus", "emotion": "작은 회복", "energy": 7}]}),
    ]


def _structure_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _option(8, "A", "정석 팝 발라드 구조", "Intro - Verse - Pre - Chorus - Verse - Pre - Chorus - Bridge - Final Chorus - Outro", {"structure_plan": {"sections": ["Intro", "Verse 1", "Pre-Chorus", "Chorus", "Verse 2", "Pre-Chorus", "Chorus", "Bridge", "Final Chorus", "Outro"], "reason": "긴장과 해소를 가장 익숙하게 전달하는 구조입니다."}}),
        _option(8, "B", "빠른 후렴 진입", "Verse를 짧게 가져가 첫 45초 안에 후렴을 보여줍니다.", {"structure_plan": {"sections": ["Intro", "Verse", "Chorus", "Verse 2", "Chorus", "Bridge", "Final Chorus"], "reason": "첫 후렴을 빨리 보여줘 스트리밍 환경의 이탈을 줄입니다."}}),
        _option(8, "C", "미니멀 서사형", "Pre-Chorus를 줄이고 Verse와 Chorus의 대비에 집중합니다.", {"structure_plan": {"sections": ["Intro", "Verse 1", "Verse 2", "Chorus", "Bridge", "Final Chorus", "Outro"], "reason": "가사와 보컬 거리감을 오래 끌고 가는 구조입니다."}}),
    ]


def _harmony_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _option(9, "A", "I - V - vi - IV 중심", "대중적이고 안정적인 회상감을 만듭니다.", {"harmony_plan": {"key": "A major", "verse": "I - V - vi - IV", "pre_chorus": "ii - V - iii - vi", "chorus": "IV - V - iii - vi", "reason": "후렴을 IV로 열어 바로 해결되지 않는 그리움을 남깁니다."}}),
        _option(9, "B", "vi - IV - I - V 중심", "마이너 감정에서 시작해 따뜻하게 열리는 느낌을 줍니다.", {"harmony_plan": {"key": "G major", "verse": "vi - IV - I - V", "pre_chorus": "IV - V - iii - vi", "chorus": "I - V - vi - IV", "reason": "벌스의 쓸쓸함과 후렴의 안정감을 명확히 대비합니다."}}),
        _option(9, "C", "I - iii - IV - V 중심", "조금 더 클래식하고 담백한 발라드 감각을 만듭니다.", {"harmony_plan": {"key": "D major", "verse": "I - iii - IV - V", "pre_chorus": "ii - V", "chorus": "IV - V - I - vi", "reason": "복잡한 차용보다 선명한 해결감으로 가사를 앞세웁니다."}}),
    ]


def _melody_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _option(10, "A", "후렴 후반 최고음", "처음부터 최고음을 쓰지 않고 두 번째 구절에서 감정 보상을 줍니다.", {"melody_direction": {"verse": "낮은 음역에서 말하듯 순차 진행", "chorus": "첫 두 마디는 짧은 반복, 후반에 최고음", "peak_note_position": "chorus second half"}}),
        _option(10, "B", "짧은 반복 모티브", "후렴 첫 마디 리듬을 반복해 따라 부르기 쉽게 만듭니다.", {"melody_direction": {"verse": "짧은 말붙임 중심", "chorus": "같은 리듬을 두 번 반복하고 두 번째에서 음역 상승", "hook_shape": "short repeat then lift"}}),
        _option(10, "C", "긴 음가 중심", "후렴에서 긴 음을 사용해 보컬 호흡과 리버브가 감정을 만들게 합니다.", {"melody_direction": {"verse": "촘촘한 말하듯 리듬", "chorus": "긴 음가와 넓은 호흡", "singability": "high"}}),
    ]


def _hook_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    titles = blueprint.get("title_candidates") or ["아직 그 밤에"]
    title = titles[0] if isinstance(titles, list) and titles else "아직 그 밤에"
    return [
        _option(11, "A", "제목 직결 후크", "후렴 첫 줄에 제목을 거의 그대로 넣어 기억성을 만듭니다.", {"hook_plan": {"hook_type": "lyric + melody hook", "hook_location": "chorus first two bars", "lyric_hook": title, "repeat_strategy": "매 후렴 반복, 마지막 후렴에서 하모니와 애드리브 추가"}}),
        _option(11, "B", "멜로디 리듬 후크", "가사보다 리듬과 음형 반복으로 각인시킵니다.", {"hook_plan": {"hook_type": "melody rhythm hook", "hook_location": "chorus opening", "melody_hook_direction": "같은 리듬을 두 번 반복하고 마지막 음만 상승", "repeat_strategy": "벌스 끝에서도 짧게 예고"}}),
        _option(11, "C", "침묵 후 진입 후크", "후렴 직전에 한 박자 비워 가사 첫 줄을 더 크게 들리게 합니다.", {"hook_plan": {"hook_type": "silence + lyric hook", "hook_location": "pre-chorus end to chorus start", "repeat_strategy": "후렴 직전 드롭아웃 후 제목 문장 진입"}}),
    ]


def _rhythm_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _option(12, "A", "72BPM 슬로우 발라드", "드럼보다 보컬 호흡과 피아노 움직임이 곡을 이끕니다.", {"rhythm_groove": {"bpm": 72, "meter": "4/4", "groove": "slow ballad groove", "verse_rhythm": "말하듯 촘촘한 보컬 리듬", "chorus_rhythm": "긴 음가 중심"}}),
        _option(12, "B", "78BPM 미디엄 발라드", "후렴에서 드럼과 베이스가 조금 더 앞으로 나옵니다.", {"rhythm_groove": {"bpm": 78, "meter": "4/4", "groove": "medium pop ballad groove", "drum_entry": "first chorus", "final_chorus_rhythm_lift": "open hi-hat and cymbal swell"}}),
        _option(12, "C", "84BPM 어쿠스틱 팝", "어쿠스틱 기타 스트럼과 가벼운 퍼커션으로 전진감을 줍니다.", {"rhythm_groove": {"bpm": 84, "meter": "4/4", "groove": "acoustic pop groove", "verse_rhythm": "guitar-led pulse", "chorus_rhythm": "steady singalong rhythm"}}),
    ]


def _arrangement_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _option(13, "A", "피아노에서 풀밴드로", "피아노와 패드로 시작해 후렴에서 드럼, 베이스, 스트링을 추가합니다.", {"arrangement_direction": {"intro": "solo piano with soft pad", "verse_1": "piano only", "pre_chorus": "low strings and subtle riser", "chorus": "drums, bass, strings", "final_chorus": "full band, backing vocals, adlibs"}}),
        _option(13, "B", "어쿠스틱 미니멀", "기타와 작은 퍼커션 중심으로 친밀한 거리감을 유지합니다.", {"arrangement_direction": {"intro": "acoustic guitar texture", "verse_1": "guitar and close vocal", "chorus": "light bass, brushed drums, pad", "final_chorus": "harmony vocals and wider guitar layers"}}),
        _option(13, "C", "모던 신스 팝 발라드", "피아노보다 패드, 서브베이스, 넓은 신스 레이어를 중심에 둡니다.", {"arrangement_direction": {"intro": "soft synth pad motif", "verse_1": "subtle pulse and vocal", "chorus": "wide synth, electronic drums, bass", "final_chorus": "stacked vocals and bright synth counterline"}}),
    ]


def _vocal_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _option(14, "A", "가까운 벌스, 열린 후렴", "벌스는 숨소리가 느껴지게, 후렴은 넓고 강하게 갑니다.", {"vocal_production": {"verse_vocal": "close and restrained", "chorus_vocal": "open and powerful", "double_tracking": "chorus only", "adlib": "final chorus ending", "effects": ["plate reverb", "slap delay"]}}),
        _option(14, "B", "담백한 싱어송라이터 톤", "더블링과 보정을 줄이고 가사 전달력을 우선합니다.", {"vocal_production": {"verse_vocal": "dry and intimate", "chorus_vocal": "natural lift", "double_tracking": "minimal", "harmony": "final chorus light harmony", "effects": ["short room reverb"]}}),
        _option(14, "C", "K-pop식 레이어 보컬", "후렴과 마지막 후렴에서 더블링, 하모니, 애드리브를 적극 사용합니다.", {"vocal_production": {"verse_vocal": "clean and centered", "chorus_vocal": "stacked and wide", "double_tracking": "chorus and final chorus", "harmony": "final chorus second half", "effects": ["plate reverb", "long delay throw"]}}),
    ]


def _mixing_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _option(15, "A", "보컬 전면 발라드 믹스", "보컬을 중앙 전면에 두고 악기는 넓게 배치합니다.", {"sound_mixing": {"mixing_direction": "보컬 중심의 넓은 발라드 믹스", "vocal_position": "front and center", "low_end": "controlled and warm", "reverb": "medium-long plate reverb", "mastering": "streaming-friendly, not overly compressed"}}),
        _option(15, "B", "따뜻한 어쿠스틱 믹스", "중역대 보컬과 기타의 온기를 살리고 과한 고역을 피합니다.", {"sound_mixing": {"mixing_direction": "warm acoustic mix", "vocal_position": "close center", "low_end": "soft and natural", "reverb": "short room plus subtle plate", "mastering": "dynamic and intimate"}}),
        _option(15, "C", "모던 팝 와이드 믹스", "스테레오 폭과 고역 광택을 더해 세련된 팝 질감을 만듭니다.", {"sound_mixing": {"mixing_direction": "modern wide pop ballad mix", "vocal_position": "front center with wide doubles", "low_end": "tight sub support", "reverb": "wide plate and delay throws", "mastering": "clear streaming loudness"}}),
    ]


def _final_options(project: dict[str, Any], blueprint: dict[str, Any], recommendation_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _option(16, "A", "프로듀서 노트형 최종안", "실제 세션을 시작할 수 있도록 구조, 코드, 편곡, 보컬 지시를 한 문서로 정리합니다.", {"final_production_guide": _final_guide(project, blueprint, "producer_note")}),
        _option(16, "B", "작곡가 스케치형 최종안", "제목, 가사, 멜로디, 코드 아이디어를 먼저 잡는 작곡 노트로 정리합니다.", {"final_production_guide": _final_guide(project, blueprint, "songwriter_sketch")}),
        _option(16, "C", "편곡·믹싱 중심 최종안", "사운드 레이어, 보컬 프로덕션, 믹싱 방향을 더 자세히 정리합니다.", {"final_production_guide": _final_guide(project, blueprint, "production_mix")}),
    ]


def _option(stage: int, code: str, label: str, summary: str, blueprint_updates: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"stage_{stage}_{code.lower()}",
        "label": f"{code}안: {label}",
        "summary": summary,
        "blueprint_updates": blueprint_updates,
    }


def _final_guide(project: dict[str, Any], blueprint: dict[str, Any], mode: str) -> str:
    concept = blueprint.get("concept", {})
    harmony = blueprint.get("harmony_plan", {})
    hook = blueprint.get("hook_plan", {})
    arrangement = blueprint.get("arrangement_direction", {})
    vocal = blueprint.get("vocal_production", {})
    mixing = blueprint.get("sound_mixing", {})
    title_candidates = blueprint.get("title_candidates") or ["가제 미정"]
    title = title_candidates[0] if isinstance(title_candidates, list) else str(title_candidates)
    genre = concept.get("genre") or project.get("target_genre") or "K-pop Ballad"
    mood = ", ".join(concept.get("mood", [])) if isinstance(concept.get("mood"), list) else concept.get("mood", "그리움")
    bpm = _read_nested(blueprint, "rhythm_groove", "bpm") or _read_nested(blueprint, "rhythm_groove", "bpm_range") or "70-80"
    base = (
        f"이번 신곡은 '{title}'을 가제로 삼고, {bpm}BPM 근처의 {genre}로 설계합니다. "
        f"핵심 정서는 {mood}이며, 컨셉은 {concept.get('new_song_concept') or concept.get('one_sentence_pitch') or '회상과 고백을 중심으로 한 새 곡'}입니다. "
        f"코드는 Verse {harmony.get('verse', 'I - V - vi - IV')}, Pre-Chorus {harmony.get('pre_chorus', 'ii - V')}, Chorus {harmony.get('chorus', 'IV - V - iii - vi')}를 후보로 두고, "
        f"후크는 {hook.get('hook_location', '후렴 첫 두 마디')}에 {hook.get('hook_type', '가사와 멜로디 후크')}를 배치합니다. "
        f"편곡은 {arrangement.get('intro', '낮은 밀도의 인트로')}에서 시작해 마지막 후렴에서 {arrangement.get('final_chorus', '보컬과 악기 레이어를 확장')}하는 방향입니다. "
        "기존 곡의 멜로디, 가사, 편곡 리프를 복제하지 말고 여러 레퍼런스에서 관찰한 창작 원리만 새 표현으로 바꿔 적용합니다."
    )
    if mode == "songwriter_sketch":
        return base + " 먼저 제목 문장과 후렴 첫 줄을 확정한 뒤, 벌스 가사는 장면 묘사로 쓰고 후렴은 직접 고백형 문장으로 좁혀 가세요."
    if mode == "production_mix":
        return (
            base
            + f" 보컬은 {vocal.get('verse_vocal', '가까운 벌스')}에서 {vocal.get('chorus_vocal', '열린 후렴')}으로 이동하고, "
            f"믹스는 {mixing.get('mixing_direction', '보컬 중심의 넓은 발라드 믹스')}를 기준으로 잡습니다."
        )
    return base


def _read_nested(data: dict[str, Any], key: str, subkey: str) -> Any:
    value = data.get(key)
    if isinstance(value, dict):
        return value.get(subkey)
    return None
