from __future__ import annotations

import re
from typing import Any


COMMON_PROGRESSIONS = {
    "I - V - vi - IV": "안정적인 팝 회상감",
    "vi - IV - I - V": "마이너 정서에서 밝게 열리는 진행",
    "IV - V - iii - vi": "후렴을 바로 해결하지 않고 감정을 열어두는 K-pop형 진행",
    "ii - V - iii - vi": "프리코러스에서 긴장과 기대감을 만드는 진행",
    "I - vi - IV - V": "클래식한 대중가요형 해결감",
    "I - iii - IV - V": "담백하고 서정적인 상승감",
}

SECTION_ALIASES = {
    "verse": "verse",
    "verse 1": "verse",
    "verse 2": "verse",
    "벌스": "verse",
    "1절": "verse",
    "2절": "verse",
    "pre": "pre_chorus",
    "pre-chorus": "pre_chorus",
    "pre chorus": "pre_chorus",
    "프리": "pre_chorus",
    "프리코러스": "pre_chorus",
    "chorus": "chorus",
    "hook": "chorus",
    "후렴": "chorus",
    "코러스": "chorus",
    "bridge": "bridge",
    "브릿지": "bridge",
    "브리지": "bridge",
    "all": "all",
    "전체": "all",
}


def analyze_harmony(chord_progression: str | None, audio_features: dict[str, Any]) -> dict[str, Any]:
    key = audio_features.get("estimated_key") or "Unknown"
    parsed = parse_progression(chord_progression)
    has_user_chords = bool(parsed)
    fallback = "I - V - vi - IV"

    verse = parsed.get("verse") or parsed.get("all") or (fallback if not has_user_chords else None)
    pre = parsed.get("pre_chorus")
    chorus = parsed.get("chorus") or parsed.get("all") or (fallback if not has_user_chords else None)
    bridge = parsed.get("bridge")
    progression_map = {
        "verse": verse,
        "pre_chorus": pre,
        "chorus": chorus,
        "bridge": bridge,
    }
    all_progressions = [value for value in progression_map.values() if value]

    section_functions = {section: analyze_progression_function(value) for section, value in progression_map.items() if value}
    borrowed = sorted({item for progression in all_progressions for item in find_borrowed_chords(progression)})
    secondary = sorted({item for progression in all_progressions for item in find_secondary_dominants(progression)})
    has_modulation = detect_modulation(chord_progression or "")

    return {
        "key": key,
        "has_user_chords": has_user_chords,
        "chord_progression_source": "user_provided" if has_user_chords else "fallback_template",
        "verse_progression": verse,
        "pre_chorus_progression": pre,
        "chorus_progression": chorus,
        "bridge_progression": bridge,
        "progression_map": progression_map,
        "section_functions": section_functions,
        "borrowed_chords": borrowed,
        "secondary_dominants": secondary,
        "has_modulation": has_modulation,
        "harmonic_mood": infer_harmonic_mood(chorus or verse or ""),
        "tension_code_role": infer_tension_role(pre, chorus, bridge),
        "opening_emotion_chord": opening_chord_role(chorus or verse),
        "closing_emotion_chord": closing_chord_role(chorus or verse),
        "familiarity": infer_familiarity(all_progressions),
        "producer_interpretation": build_harmony_interpretation(progression_map, has_user_chords),
        "creative_principle": build_creative_principle(progression_map, has_user_chords),
        "analysis_note": (
            "사용자 제공 코드 진행을 섹션별로 분석했습니다."
            if has_user_chords
            else "코드 진행 입력이 없어 장르 범용 진행을 예시로 표시합니다. 실제 통계에는 사용자 제공 코드가 있는 곡만 반영하는 것이 좋습니다."
        ),
        "data_confidence": {
            "chord_progression": {
                "confidence": "medium" if has_user_chords else "low",
                "source": "user-provided chord progression" if has_user_chords else "fallback template",
            }
        },
    }


def parse_progression(chord_progression: str | None) -> dict[str, str]:
    if not chord_progression or not chord_progression.strip():
        return {}

    result: dict[str, str] = {}
    normalized_text = chord_progression.replace("→", " - ").replace("—", " - ").replace("–", " - ")
    for part in re.split(r"[\n;]+", normalized_text):
        line = part.strip()
        if not line:
            continue
        section, value = split_section_line(line)
        normalized_value = normalize_progression(value)
        if not normalized_value:
            continue
        result[section] = normalized_value
    return result


def split_section_line(line: str) -> tuple[str, str]:
    if ":" in line:
        raw_section, value = line.split(":", 1)
        return normalize_section(raw_section), value.strip()

    match = re.match(r"^(verse|pre[- ]?chorus|pre|chorus|hook|bridge|벌스|프리코러스|후렴|코러스|브릿지|브리지|전체)\s+(.+)$", line, flags=re.IGNORECASE)
    if match:
        return normalize_section(match.group(1)), match.group(2).strip()
    return "all", line


def normalize_section(value: str) -> str:
    cleaned = value.strip().lower()
    return SECTION_ALIASES.get(cleaned, "all")


def normalize_progression(value: str) -> str:
    cleaned = value.strip()
    cleaned = re.sub(r"\s+/\s+", " - ", cleaned)
    cleaned = re.sub(r"\s*(?:-|,|\|)\s*", " - ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.replace(" - - ", " - ")
    return cleaned.strip(" -")


def analyze_progression_function(progression: str) -> dict[str, Any]:
    chords = split_chords(progression)
    return {
        "chords": chords,
        "length": len(chords),
        "starts_with": chords[0] if chords else None,
        "ends_with": chords[-1] if chords else None,
        "start_role": chord_role(chords[0]) if chords else None,
        "end_role": chord_role(chords[-1]) if chords else None,
        "contains_minor_color": any(chord.lower().startswith(("vi", "iii", "ii")) for chord in chords),
        "contains_opening_subdominant": any(chord.startswith("IV") or chord.lower().startswith("iv") for chord in chords),
        "contains_dominant_tension": any(chord.startswith("V") or "V/" in chord for chord in chords),
        "emotional_function": progression_emotional_function(chords),
    }


def split_chords(progression: str) -> list[str]:
    return [item.strip() for item in re.split(r"\s+-\s+", progression) if item.strip()]


def find_borrowed_chords(progression: str) -> list[str]:
    chords = split_chords(progression)
    borrowed = []
    for chord in chords:
        if chord.startswith(("b", "♭")) or chord in {"iv", "bVI", "bVII", "♭VI", "♭VII"}:
            borrowed.append(chord)
    return borrowed


def find_secondary_dominants(progression: str) -> list[str]:
    return [chord for chord in split_chords(progression) if "/" in chord and chord.upper().startswith("V")]


def detect_modulation(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ["modulation", "key change", "전조", "키체인지"])


def infer_harmonic_mood(progression: str) -> list[str]:
    chords = split_chords(progression)
    moods = []
    if any(chord.lower().startswith("vi") or chord.lower().startswith("iii") for chord in chords):
        moods.extend(["그리움", "감정적 여운"])
    if any(chord.startswith("IV") for chord in chords):
        moods.append("열린 감정")
    if any(chord.startswith("V") for chord in chords):
        moods.append("긴장과 해결 기대")
    if any(chord.startswith("I") for chord in chords):
        moods.append("안정감")
    return list(dict.fromkeys(moods)) or ["화성 기능 추가 확인 필요"]


def infer_tension_role(pre: str | None, chorus: str | None, bridge: str | None) -> str:
    if pre and ("V" in pre or "ii" in pre):
        return "Pre-Chorus에서 ii/V 계열로 후렴 전 긴장을 만드는 구조입니다."
    if chorus and split_chords(chorus) and split_chords(chorus)[0].startswith("IV"):
        return "후렴을 IV 계열로 열어 바로 해결하지 않고 감정을 확장합니다."
    if bridge and detect_modulation(bridge):
        return "Bridge에서 전조 또는 키 변화로 마지막 후렴의 리프트를 만들 수 있습니다."
    return "명확한 긴장 코드는 입력만으로 확정하기 어렵지만, V 또는 ii-V를 후렴 직전에 배치하는 전략을 검토할 수 있습니다."


def opening_chord_role(progression: str | None) -> str:
    if not progression:
        return "미확정"
    first = split_chords(progression)[0]
    return f"{first}: {chord_role(first)}"


def closing_chord_role(progression: str | None) -> str:
    if not progression:
        return "미확정"
    last = split_chords(progression)[-1]
    return f"{last}: {chord_role(last)}"


def chord_role(chord: str) -> str:
    normalized = chord.strip()
    if normalized.startswith("I") and not normalized.lower().startswith(("ii", "iii", "iv")):
        return "안정과 귀환"
    if normalized.lower().startswith("vi"):
        return "그리움과 여운"
    if normalized.startswith("IV") or normalized.lower().startswith("iv"):
        return "감정을 여는 서브도미넌트"
    if normalized.startswith("V"):
        return "긴장과 해결 기대"
    if normalized.lower().startswith("ii"):
        return "다음 화음으로 미는 준비 긴장"
    if normalized.lower().startswith("iii"):
        return "중간색의 연결과 아련함"
    return "색채 화음"


def progression_emotional_function(chords: list[str]) -> str:
    if not chords:
        return "분석 불가"
    if chords[0].startswith("IV"):
        return "처음부터 결론을 내리지 않고 감정을 열어두는 진행"
    if chords[0].lower().startswith("vi"):
        return "마이너 정서에서 출발해 회상감을 만드는 진행"
    if chords[0].startswith("I") and chords[-1].startswith("IV"):
        return "안정에서 출발해 열린 여운을 남기는 진행"
    if chords[-1].startswith("I"):
        return "마지막에 안정적으로 해결하는 진행"
    return "반복을 통해 정서를 고정하는 진행"


def infer_familiarity(progressions: list[str]) -> dict[str, Any]:
    matched = []
    for progression in progressions:
        for common, description in COMMON_PROGRESSIONS.items():
            if normalize_progression(progression).lower() == common.lower():
                matched.append({"progression": common, "description": description})
    if matched:
        return {"level": "high", "matched_patterns": matched, "interpretation": "대중음악에서 익숙한 진행이라 청자가 빠르게 받아들이기 좋습니다."}
    if progressions:
        return {"level": "medium", "matched_patterns": [], "interpretation": "완전한 클리셰보다는 사용자 입력에 따른 개별 진행으로 보입니다."}
    return {"level": "unknown", "matched_patterns": [], "interpretation": "코드 입력이 필요합니다."}


def build_harmony_interpretation(progression_map: dict[str, str | None], has_user_chords: bool) -> str:
    if not has_user_chords:
        return "코드 진행이 입력되지 않아 실제 곡의 화성 설계는 확정할 수 없습니다. 코드나 악보 정보를 입력하면 섹션별 긴장과 해결을 분석합니다."
    chorus = progression_map.get("chorus")
    verse = progression_map.get("verse")
    if chorus and verse and chorus != verse:
        return f"Verse의 {verse}와 Chorus의 {chorus}가 다르게 설계되어 파트 전환의 감정 차이를 만들 수 있습니다."
    if chorus:
        return f"후렴 진행 {chorus}가 곡의 핵심 감정을 반복적으로 고정하는 역할을 합니다."
    return "입력된 코드 진행을 바탕으로 섹션별 기능을 정리했습니다."


def build_creative_principle(progression_map: dict[str, str | None], has_user_chords: bool) -> str:
    if not has_user_chords:
        return "레퍼런스곡의 코드를 추정으로 단정하지 말고, 사용자가 확인한 코드나 공개 악보 정보를 입력한 뒤 통계에 반영하세요."
    chorus = progression_map.get("chorus") or "후렴 진행"
    return (
        f"{chorus} 자체를 베끼기보다 첫 화음이 감정을 여는지, 마지막 화음이 해결하는지, "
        "Pre-Chorus가 긴장을 충분히 만드는지를 새 멜로디와 새 가사에 맞게 변형하세요."
    )
