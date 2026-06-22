def analyze_vocal(metadata: dict, lyrics_analysis: dict) -> dict:
    genre = metadata.get("genre") or "Pop"
    return {
        "vocal_tone": "warm and emotional" if "Ballad" in genre or "발라드" in genre else "clear and forward",
        "verse_delivery": "intimate and restrained",
        "chorus_delivery": "open and memorable",
        "vocal_effects": ["reverb", "delay", "doubling"],
        "adlib_usage": "final chorus 후보",
        "title_delivery": "제목 또는 핵심 문장은 후렴 첫 구절에서 또렷하게 전달하는 편이 좋습니다.",
        "creative_principle": "보컬 톤의 거리감과 감정 상승 방식만 참고하고 특정 가창 애드리브를 복제하지 않습니다.",
    }


def analyze_mixing(audio_features: dict) -> dict:
    loudness = float(audio_features.get("loudness_estimate", -20))
    centroid = float(audio_features.get("spectral_centroid_mean", 0))
    return {
        "vocal_position": "front",
        "low_end_density": "controlled" if loudness < -12 else "dense",
        "stereo_width": "wide chorus / focused verse 후보",
        "reverb_amount": "medium-high" if centroid < 2500 else "medium",
        "mastering_loudness_style": infer_loudness_style(loudness),
        "radio_streaming_fit": "스트리밍 친화적 음압을 목표로 하되 과도한 압축은 피하는 방향",
        "creative_principle": "음압과 공간감의 경향만 참고하고, 특정 마스터 질감을 복제하려 하지 않습니다.",
    }


def infer_loudness_style(loudness: float) -> str:
    if loudness < -24:
        return "quiet demo/reference"
    if loudness < -14:
        return "modern streaming balanced"
    return "loud commercial pop"
