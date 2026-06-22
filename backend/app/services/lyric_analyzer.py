from __future__ import annotations

import re
from collections import Counter
from typing import Any


SECTION_ALIASES = {
    "intro": "intro",
    "인트로": "intro",
    "verse": "verse",
    "verse 1": "verse",
    "verse 2": "verse",
    "벌스": "verse",
    "절": "verse",
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
    "outro": "outro",
    "아웃트로": "outro",
}

DIRECT_EMOTION_WORDS = [
    "사랑",
    "그리워",
    "보고 싶",
    "미안",
    "아파",
    "슬퍼",
    "외로",
    "기다",
    "돌아",
    "잊지",
    "miss",
    "love",
    "sorry",
    "alone",
    "cry",
]

IMAGE_WORDS = ["밤", "비", "눈", "바람", "창", "길", "계절", "불빛", "달", "새벽", "문", "거리", "꿈", "하늘"]


def analyze_lyrics(lyrics_text: str | None, title: str | None = None) -> dict[str, Any]:
    text = (lyrics_text or "").strip()
    if not text:
        return {
            "lyrics_provided": False,
            "lyric_point_of_view": "가사 미입력",
            "lyric_theme": "가사 텍스트가 없어 테마와 핵심 문장을 확정할 수 없습니다.",
            "emotion_curve": ["정보 부족"],
            "title_usage": "가사 미입력",
            "core_message": "가사를 입력하면 핵심 문장과 후크 후보를 추출합니다.",
            "key_phrase_candidates": [],
            "repeated_key_phrases": [],
            "chorus_candidate_lines": [],
            "section_summary": {},
            "chorus_key_phrase_type": "미확정",
            "metaphor_level": "unknown",
            "story_flow": "가사 입력이 필요합니다.",
            "creative_principle": "가사를 입력하면 제목과 연결되는 새 후렴 문장, 반복 문장, 감정 상승 구조를 분석할 수 있습니다.",
            "data_confidence": {"lyrics": {"confidence": "low", "source": "no lyrics provided"}},
        }

    lines = _clean_lines(text)
    sections = parse_lyric_sections(text)
    repeated = find_repeated_phrases(lines)
    key_phrase_candidates = find_key_phrase_candidates(lines, title=title, repeated=repeated, sections=sections)
    chorus_candidates = infer_chorus_candidate_lines(lines, repeated, sections)
    title_usage = infer_title_usage(text, sections, repeated, title)
    emotion_curve = infer_emotion_curve(text, sections)
    theme = infer_lyric_theme(text)
    metaphor_level = infer_metaphor_level(text)

    return {
        "lyrics_provided": True,
        "line_count": len(lines),
        "section_map": sections,
        "section_summary": summarize_sections(sections),
        "lyric_point_of_view": infer_point_of_view(text),
        "addressee": infer_addressee(text),
        "situation": infer_situation(text, theme),
        "lyric_theme": theme,
        "core_message": key_phrase_candidates[0]["line"] if key_phrase_candidates else summarize_core_message(theme, emotion_curve),
        "emotion_curve": emotion_curve,
        "verse_role": "상황, 화자, 감정의 출발점을 설명하는 구간입니다.",
        "pre_chorus_role": "후렴으로 넘어가기 전 감정의 압력이나 질문을 높이는 구간입니다.",
        "chorus_role": "곡의 핵심 감정을 가장 짧고 기억하기 쉬운 문장으로 고정하는 구간입니다.",
        "bridge_role": "반복된 감정을 다른 시점이나 더 솔직한 고백으로 전환하는 후보 구간입니다.",
        "title_usage": title_usage,
        "repeated_key_phrases": repeated,
        "key_phrase_candidates": key_phrase_candidates,
        "chorus_candidate_lines": chorus_candidates,
        "chorus_key_phrase_type": infer_key_phrase_type(key_phrase_candidates, text, title),
        "metaphor_level": metaphor_level,
        "expression_balance": infer_expression_balance(text),
        "memorable_expression_style": infer_expression_style(metaphor_level),
        "chorus_emotion_peak": emotion_curve[-1] if emotion_curve else "미확정",
        "story_flow": build_story_flow(sections, emotion_curve, key_phrase_candidates),
        "creative_principle": (
            "원문 표현을 그대로 가져오지 말고, 핵심 문장이 어떤 기능을 하는지만 참고하세요. "
            "새 곡에서는 같은 감정 기능을 새로운 제목, 새로운 이미지, 새로운 후렴 문장으로 다시 설계해야 합니다."
        ),
        "data_confidence": {"lyrics": {"confidence": "medium", "source": "user-provided lyrics"}},
    }


def parse_lyric_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"all": []}
    current = "all"
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        detected = _detect_section_header(line)
        if detected:
            current = detected
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
        sections["all"].append(line)
    return sections


def find_repeated_phrases(lines: list[str]) -> list[str]:
    normalized_to_original: dict[str, str] = {}
    counts: Counter[str] = Counter()
    for line in lines:
        normalized = _normalize_line(line)
        if len(normalized) < 3:
            continue
        normalized_to_original.setdefault(normalized, line)
        counts[normalized] += 1
    return [normalized_to_original[line] for line, count in counts.most_common(8) if count > 1]


def find_key_phrase_candidates(
    lines: list[str],
    title: str | None,
    repeated: list[str],
    sections: dict[str, list[str]],
) -> list[dict[str, Any]]:
    repeated_set = {_normalize_line(line) for line in repeated}
    chorus_set = {_normalize_line(line) for line in sections.get("chorus", [])}
    title_value = _normalize_line(title or "")
    candidates = []
    for line in lines:
        normalized = _normalize_line(line)
        if len(normalized) < 3:
            continue
        score = 0
        reasons = []
        if normalized in repeated_set:
            score += 5
            reasons.append("반복 문장")
        if normalized in chorus_set:
            score += 4
            reasons.append("후렴 구간")
        if title_value and title_value in normalized:
            score += 4
            reasons.append("제목 포함")
        if any(word in normalized for word in DIRECT_EMOTION_WORDS):
            score += 2
            reasons.append("직접 감정어")
        if 5 <= len(line) <= 36:
            score += 2
            reasons.append("후크로 쓰기 좋은 길이")
        if any(word in normalized for word in IMAGE_WORDS):
            score += 1
            reasons.append("이미지 단어")
        if score > 0:
            candidates.append({"line": line, "score": score, "reasons": reasons})
    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates[:8]


def infer_chorus_candidate_lines(lines: list[str], repeated: list[str], sections: dict[str, list[str]]) -> list[str]:
    if sections.get("chorus"):
        return sections["chorus"][:8]
    if repeated:
        return repeated[:8]
    midpoint = max(0, len(lines) // 2 - 2)
    return lines[midpoint : midpoint + 4]


def summarize_sections(sections: dict[str, list[str]]) -> dict[str, str]:
    summary = {}
    for key in ["intro", "verse", "pre_chorus", "chorus", "bridge", "outro"]:
        values = sections.get(key) or []
        if not values:
            continue
        sample = " / ".join(values[:2])
        summary[key] = f"{len(values)}줄. 대표 문장: {sample}"
    return summary


def infer_title_usage(text: str, sections: dict[str, list[str]], repeated: list[str], title: str | None) -> str:
    if not title:
        return "제목 힌트가 없어 확인 불가"
    title_value = _normalize_line(title)
    if not title_value:
        return "제목 힌트가 없어 확인 불가"
    chorus_text = _normalize_line(" ".join(sections.get("chorus", [])))
    repeated_text = _normalize_line(" ".join(repeated))
    full_text = _normalize_line(text)
    if title_value in chorus_text:
        return "후렴에 제목이 직접 등장"
    if title_value in repeated_text:
        return "반복 문장에 제목이 등장"
    if title_value in full_text:
        return "가사 전체에는 제목이 등장하지만 후렴 연결은 추가 확인 필요"
    return "제목 직접 사용은 확인되지 않음"


def infer_point_of_view(text: str) -> str:
    normalized = _normalize_line(text)
    first_person = ["나는", "내가", "나를", "내게", "우리", "i ", "i'm", "me ", "my "]
    second_person = ["너는", "네가", "너를", "너에게", "그대", "you", "your"]
    if any(token in normalized for token in first_person):
        return "1인칭 화자"
    if any(token in normalized for token in second_person):
        return "2인칭 대상에게 말하는 화자"
    return "상황과 감정 중심의 화자"


def infer_addressee(text: str) -> str:
    normalized = _normalize_line(text)
    if any(token in normalized for token in ["너", "그대", "you", "baby"]):
        return "사랑하거나 떠나간 대상"
    if any(token in normalized for token in ["나", "myself", "my self"]):
        return "자기 자신"
    return "명시되지 않은 대상"


def infer_situation(text: str, theme: str) -> str:
    normalized = _normalize_line(text)
    if any(token in normalized for token in ["이별", "떠나", "헤어", "goodbye", "farewell"]):
        return "이별 이후의 감정을 돌아보는 상황"
    if any(token in normalized for token in ["밤", "새벽", "길", "창"]):
        return "특정 이미지나 시간대를 통해 감정을 꺼내는 상황"
    return f"{theme}를 중심으로 감정을 전개하는 상황"


def infer_lyric_theme(text: str) -> str:
    normalized = _normalize_line(text)
    rules = [
        ("이별 후 그리움", ["이별", "헤어", "떠나", "그리워", "보고 싶", "miss", "missing", "goodbye"]),
        ("사랑 고백", ["사랑", "좋아", "love", "heart", "forever"]),
        ("후회와 미련", ["미안", "후회", "못했", "돌아", "아직", "sorry", "regret"]),
        ("회복과 다짐", ["괜찮", "다시", "일어나", "꿈", "hope", "rise"]),
        ("자신감과 해방", ["자유", "빛나", "dance", "party", "tonight", "fire"]),
    ]
    for theme, needles in rules:
        if any(needle in normalized for needle in needles):
            return theme
    return "관계와 감정의 변화"


def infer_emotion_curve(text: str, sections: dict[str, list[str]]) -> list[str]:
    normalized = _normalize_line(text)
    if sections.get("chorus"):
        base = ["상황 제시", "감정 상승", "핵심 고백"]
    else:
        base = ["도입", "전개", "집중"]
    if any(token in normalized for token in ["이별", "그리워", "보고 싶", "miss", "alone"]):
        return [base[0], "그리움", "후회", "고백"]
    if any(token in normalized for token in ["사랑", "love", "forever"]):
        return [base[0], "끌림", "확신", "고백"]
    if any(token in normalized for token in ["다시", "괜찮", "hope", "rise"]):
        return [base[0], "흔들림", "회복", "다짐"]
    return [*base, "해소"]


def infer_key_phrase_type(candidates: list[dict[str, Any]], text: str, title: str | None) -> str:
    if not candidates:
        return "핵심 문장 미확정"
    top = candidates[0]
    reasons = set(top.get("reasons", []))
    if "제목 포함" in reasons:
        return "제목 반복 후크"
    if "반복 문장" in reasons and "직접 감정어" in reasons:
        return "가사 후크 + 직접 고백형"
    if "반복 문장" in reasons:
        return "반복 가사 후크"
    if any(word in _normalize_line(text) for word in IMAGE_WORDS):
        return "이미지 기반 후크"
    if title:
        return "제목 연결 후보"
    return "정서 요약형 후크"


def infer_metaphor_level(text: str) -> str:
    normalized = _normalize_line(text)
    image_count = sum(1 for token in IMAGE_WORDS if token in normalized)
    direct_count = sum(1 for token in DIRECT_EMOTION_WORDS if token in normalized)
    if image_count >= 4 and image_count > direct_count:
        return "high"
    if image_count >= 2:
        return "medium"
    return "low"


def infer_expression_balance(text: str) -> str:
    normalized = _normalize_line(text)
    image_count = sum(1 for token in IMAGE_WORDS if token in normalized)
    direct_count = sum(1 for token in DIRECT_EMOTION_WORDS if token in normalized)
    if direct_count > image_count:
        return "직접 표현 중심"
    if image_count > direct_count:
        return "이미지/은유 중심"
    return "직접 표현과 이미지가 균형"


def infer_expression_style(metaphor_level: str) -> str:
    if metaphor_level == "high":
        return "이미지와 은유를 통해 감정을 우회적으로 각인합니다."
    if metaphor_level == "medium":
        return "직접 감정과 장면 이미지를 섞어 기억점을 만듭니다."
    return "직접적인 감정 문장으로 청자가 빠르게 이해하도록 설계되어 있습니다."


def build_story_flow(sections: dict[str, list[str]], emotion_curve: list[str], candidates: list[dict[str, Any]]) -> str:
    if sections.get("chorus"):
        hook = candidates[0]["line"] if candidates else "후렴 핵심 문장"
        return f"Verse에서 상황을 만들고, Chorus에서 '{hook}' 같은 핵심 문장으로 감정을 고정하는 흐름입니다."
    return f"명확한 섹션 표기는 없지만 감정선은 {' -> '.join(emotion_curve)} 흐름으로 정리할 수 있습니다."


def summarize_core_message(theme: str, emotion_curve: list[str]) -> str:
    return f"{theme}를 {' -> '.join(emotion_curve[-2:])} 방향으로 전달하는 가사입니다."


def _clean_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip() and not _detect_section_header(line.strip())]


def _detect_section_header(line: str) -> str | None:
    cleaned = re.sub(r"^[\[\(]|[\]\)]$", "", line.strip()).strip().lower()
    cleaned = cleaned.rstrip(":")
    return SECTION_ALIASES.get(cleaned)


def _normalize_line(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()
