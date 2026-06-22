from __future__ import annotations

from statistics import mean
from typing import Any

from app.services.research_service import describe_research_policy, search_reference_songs


def build_reference_recommendations(
    project: dict[str, Any],
    songs: list[dict[str, Any]],
    analyses: list[dict[str, Any]],
    user_goal: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Build reference recommendations from local analysis data plus MVP mock research data."""
    local_references = [_song_to_reference(song, analyses) for song in songs]
    mock_references = search_reference_songs(
        goal=user_goal or _project_goal_text(project),
        genre=project.get("target_genre"),
        mood=project.get("target_mood"),
        limit=limit,
    )

    combined = _dedupe_references(local_references + mock_references)[:limit]
    return {
        "recommendations": [
            {
                "id": item["id"],
                "title": item["title"],
                "artist": item.get("artist"),
                "genre": item.get("genre"),
                "country": item.get("country"),
                "bpm": item.get("bpm"),
                "key": item.get("key"),
                "hook_type": item.get("hook_type"),
                "reason": _recommendation_reason(project, item),
                "creative_use": item.get("creative_principle") or "곡의 표면을 복제하지 말고 구조와 감정 설계 원리만 참고합니다.",
                "avoid_copying": item.get("avoid_copying")
                or ["멜로디, 가사, 특정 리프를 그대로 사용하지 않습니다.", "여러 곡의 공통 원리로 일반화해 새 곡에 적용합니다."],
            }
            for item in combined
        ],
        "common_patterns": _common_patterns(combined, analyses),
        "creative_principles": _creative_principles(combined),
        "plagiarism_risks": [
            "특정 곡의 후렴 멜로디 윤곽을 그대로 따라 하면 표절 위험이 커집니다.",
            "가사 핵심 문장, 제목 사용 방식, 편곡 리프는 직접 차용하지 않습니다.",
            "한 곡만 기준으로 삼지 말고 여러 곡의 공통 원리를 추출해 새 표현으로 바꿉니다.",
        ],
        "research_policy": describe_research_policy(),
    }


def _song_to_reference(song: dict[str, Any], analyses: list[dict[str, Any]]) -> dict[str, Any]:
    analysis = next((item for item in analyses if item.get("song_id") == song.get("id")), None)
    hook = analysis.get("hook", {}) if analysis else {}
    takeaway = analysis.get("takeaway", {}) if analysis else {}
    return {
        "id": song["id"],
        "title": song.get("title") or "Untitled",
        "artist": song.get("artist"),
        "genre": song.get("genre"),
        "country": song.get("country"),
        "release_year": song.get("release_year"),
        "bpm": song.get("bpm"),
        "key": song.get("key"),
        "mood": analysis.get("concept", {}).get("mood", []) if analysis else [],
        "hook_type": hook.get("primary_hook_type") or hook.get("hook_type") or "분석된 후크",
        "structure": " - ".join(analysis.get("structure", {}).get("structure", [])) if analysis else None,
        "why_it_matters": "사용자가 직접 분석한 라이브러리 곡이므로 새 프로젝트의 기준점으로 삼기 좋습니다.",
        "creative_principle": "; ".join(takeaway.get("transferable_principles", [])[:2])
        or "분석 데이터에서 확인한 BPM, Key, 구조, 후크 성향을 새 곡의 방향성 참고로 사용합니다.",
        "avoid_copying": takeaway.get("avoid_copying", []) if analysis else [],
    }


def _recommendation_reason(project: dict[str, Any], reference: dict[str, Any]) -> str:
    genre = project.get("target_genre") or "새 프로젝트"
    mood = project.get("target_mood") or "목표 감정"
    bpm = reference.get("bpm")
    tempo_text = f"약 {bpm}BPM" if bpm else "비슷한 템포 감각"
    return (
        f"{reference['title']}은 {tempo_text}와 {reference.get('hook_type', '후크 설계')}가 {genre}의 {mood} 방향을 잡는 데 도움이 됩니다. "
        "표면을 모방하기보다 감정 상승 방식과 후렴 기억 장치를 참고하세요."
    )


def _common_patterns(references: list[dict[str, Any]], analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bpms = [float(item["bpm"]) for item in references if item.get("bpm") is not None]
    hook_types = _count_values(item.get("hook_type") for item in references)
    structures = [item.get("structure") for item in references if item.get("structure")]
    patterns = [
        {
            "pattern_type": "tempo",
            "description": f"선택된 레퍼런스는 평균 약 {round(mean(bpms)) if bpms else 72}BPM 근처의 느린-미디엄 템포에 모입니다.",
            "creative_use": "빠른 드럼보다 보컬 호흡, 코드 전환, 후렴 레이어 증가로 에너지를 설계합니다.",
            "confidence": "medium" if bpms else "low",
        },
        {
            "pattern_type": "hook",
            "description": f"가장 많이 보이는 후크 유형은 {hook_types[0]['label'] if hook_types else '가사+멜로디 후크'}입니다.",
            "creative_use": "후렴 첫 두 마디에 제목 또는 핵심 감정을 새 문장으로 배치해 기억성을 만듭니다.",
            "confidence": "medium",
        },
        {
            "pattern_type": "structure",
            "description": structures[0] if structures else "Verse에서 절제하고 Chorus와 Final Chorus에서 감정을 확장하는 구조가 적합합니다.",
            "creative_use": "마지막 후렴에는 애드리브, 하모니, 넓은 악기 레이어를 추가하되 기존 곡의 리프는 복제하지 않습니다.",
            "confidence": "medium" if structures or analyses else "low",
        },
    ]
    return patterns


def _creative_principles(references: list[dict[str, Any]]) -> list[str]:
    principles = [item.get("creative_principle") for item in references if item.get("creative_principle")]
    if principles:
        return principles[:5]
    return [
        "벌스는 악기 밀도를 낮춰 이야기를 선명하게 전달합니다.",
        "후렴 첫 줄에 제목과 연결되는 짧은 새 문장을 배치합니다.",
        "마지막 후렴은 보컬과 편곡을 확장해 감정적 보상을 만듭니다.",
    ]


def _dedupe_references(references: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for reference in references:
        key = f"{reference.get('title')}::{reference.get('artist')}"
        if key in seen:
            continue
        seen.add(key)
        output.append(reference)
    return output


def _project_goal_text(project: dict[str, Any]) -> str:
    return " ".join(
        str(value)
        for value in [
            project.get("title"),
            project.get("target_genre"),
            project.get("target_mood"),
            project.get("theme"),
            project.get("vocal_style"),
            project.get("bpm_range"),
        ]
        if value
    )


def _count_values(values: Any) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for value in values:
        if not value:
            continue
        counts[str(value)] = counts.get(str(value), 0) + 1
    return [{"label": key, "count": value} for key, value in sorted(counts.items(), key=lambda item: item[1], reverse=True)]
