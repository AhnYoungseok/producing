def analyze_hook(lyrics_analysis: dict, metadata: dict, audio_features: dict) -> dict:
    title = metadata.get("title") or "제목 미정"
    repeated = lyrics_analysis.get("repeated_key_phrases", [])
    primary = "lyric + melody hook" if repeated or title != "제목 미정" else "melody/rhythm hook"
    return {
        "primary_hook_type": primary,
        "hook_location": "chorus first two bars 후보",
        "hook_length": "2 bars",
        "hook_repeat_count": max(2, len(repeated) + 2),
        "hook_memorability": infer_memorability(audio_features, repeated),
        "title_hook_connection": "strong" if title and lyrics_analysis.get("title_usage") == "제목이 가사에 직접 등장" else "medium",
        "lyric_hook_candidates": repeated[:3] or [f"{title}와 연결되는 새로운 핵심 문장"],
        "repeat_strategy": "후렴마다 같은 의미의 핵심 문장을 반복하되 마지막 후렴에서는 보컬 애드리브와 편곡 확장으로 변주합니다.",
        "creative_principle": "후크의 위치와 반복 원리만 참고하고, 기존 곡의 멜로디·가사 후크는 직접 차용하지 않습니다.",
    }


def infer_memorability(audio_features: dict, repeated: list[str]) -> str:
    if repeated:
        return "high"
    if float(audio_features.get("onset_density", 0)) > 3:
        return "medium-high"
    return "medium"
