from __future__ import annotations

from typing import Any

from app.services.producer_report import PRODUCER_SECTION_ORDER, generate_producer_sections, generate_producer_summary


def generate_full_report(
    sections: dict[str, Any],
    metadata: dict[str, Any],
    audio_features: dict[str, Any],
    research_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = generate_producer_summary(sections, metadata, audio_features, research_profile)
    producer_sections = generate_producer_sections(sections, metadata, audio_features, research_profile)
    bpm = float(audio_features.get("bpm", 0) or 0)
    key = audio_features.get("estimated_key") or sections.get("harmony", {}).get("key") or "Unknown"

    return {
        "summary": summary,
        "report_style": "producer_observation_interpretation_application",
        "section_order": PRODUCER_SECTION_ORDER,
        "producer_sections": producer_sections,
        "core_reading": (
            f"이 곡은 {bpm:.1f}BPM, {key} 기준으로 정리됩니다. "
            "수치는 출처와 신뢰도를 함께 봐야 하며, 실제 창작에는 곡의 감정 기능과 에너지 설계를 일반화해서 적용해야 합니다."
        ),
        "copyright_and_copy_notice": (
            "이 분석은 기존 곡을 복제하거나 표절하기 위한 자료가 아닙니다. "
            "멜로디, 가사, 특정 리프, 사운드 시그니처를 그대로 가져오지 말고 창작 원리만 참고해야 합니다."
        ),
        "youtube_policy_notice": (
            "YouTube 링크는 레퍼런스 식별과 허용된 메타데이터 수집에만 사용됩니다. "
            "YouTube 오디오는 다운로드, 추출, 분리, 변환, 캡처, 분석하지 않습니다."
        ),
        "transferable_principles": sections.get("takeaway", {}).get("transferable_principles", []),
        "anti_copy_notice": (
            "원곡의 멜로디 라인, 가사 문장, 특정 편곡 리프, 보컬 애드리브, 사운드 시그니처를 복제하거나 그대로 사용하지 마세요. "
            "여러 레퍼런스의 공통 패턴을 일반화해 새로운 곡의 컨셉, 구조, 후크, 편곡 방향으로 변형해야 합니다."
        ),
    }


def build_hit_factor(sections: dict[str, Any], audio_features: dict[str, Any]) -> dict[str, Any]:
    hook = sections["hook"]
    structure = sections["structure"]
    lyrics = sections["lyrics"]
    first_chorus_time = structure.get("first_chorus_time")
    onset_density = float(audio_features.get("onset_density", 0) or 0)
    hook_type = hook.get("primary_hook_type") or "lyric + melody hook"
    title_usage = lyrics.get("title_usage") or "title usage unknown"

    return {
        "main_hit_factor": f"{hook_type}와 후렴 진입 구조의 결합",
        "singalong_level": hook.get("hook_memorability", "medium"),
        "emotional_identification": "strong" if lyrics.get("lyric_point_of_view") in ["1인칭 화자", "1st person"] else "medium",
        "first_30_seconds_impact": "medium-high" if onset_density > 2 else "medium",
        "chorus_entry_timing": first_chorus_time,
        "title_memorability": "high" if "chorus" in str(title_usage).lower() or "후렴" in str(title_usage) else "medium",
        "short_form_potential": "medium-high" if hook.get("hook_location") else "medium",
        "live_moment": "final chorus lift / adlib 후보",
        "replay_factor": "high" if first_chorus_time and float(first_chorus_time) < 70 else "medium",
        "creative_principle": (
            "대중성은 특정 멜로디 복제가 아니라 짧은 후크, 명확한 후렴 진입, 감정 상승 구조가 맞물릴 때 강해집니다."
        ),
    }


def build_takeaway(sections: dict[str, Any]) -> dict[str, Any]:
    hook_type = sections.get("hook", {}).get("primary_hook_type") or "가사+멜로디 후크"
    arrangement = sections.get("arrangement", {}).get("arrangement_build") or "점진적 레이어링"
    chorus_progression = sections.get("harmony", {}).get("chorus_progression") or "후렴 코드 진행 미확정"

    return {
        "transferable_principles": [
            "초반에는 정보량을 조절해 보컬, 가사, 핵심 정서가 먼저 들리게 만든다.",
            f"후렴 첫 두 마디에는 {hook_type}를 새 문장과 새 멜로디로 설계한다.",
            f"편곡은 {arrangement} 원리를 참고하되 특정 리프나 사운드 시그니처는 복제하지 않는다.",
            f"화성은 {chorus_progression}의 감정 기능을 참고하되 진행 자체보다 긴장과 해소 위치를 새롭게 설계한다.",
            "마지막 후렴에서는 보컬 애드리브, 하모니, 드럼, 스트링, 신스 중 하나 이상을 확장해 이전 후렴과 차이를 만든다.",
        ],
        "avoid_copying": [
            "기존 곡의 멜로디 라인을 그대로 사용하지 않는다.",
            "가사 문장을 직접 차용하지 않는다.",
            "특정 편곡 리프나 사운드 시그니처를 그대로 복제하지 않는다.",
            "보컬 애드리브, 콜앤리스폰스, 제목 반복 방식을 원곡과 같은 위치와 형태로 베끼지 않는다.",
        ],
        "creative_use": (
            "분석 데이터는 작곡 의사결정 체크리스트로 사용하세요. 컨셉, 감정선, 후렴 첫 두 마디, 코드 긴장/해소, 마지막 후렴 확장을 순서대로 설계하면 됩니다."
        ),
        "recommended_strategy": (
            "컨셉 한 줄을 먼저 정하고, Verse에서 절제한 뒤 Chorus에서 제목형 후크를 제시하며, Final Chorus에서 보컬과 레이어를 확장하는 전략을 우선 실험하세요."
        ),
    }
