def analyze_melody(audio_features: dict, lyrics_analysis: dict) -> dict:
    bpm = float(audio_features.get("bpm", 0))
    key = audio_features.get("estimated_key", "Unknown")
    return {
        "melody_range": "MVP 자동 음역 추출 미지원",
        "chorus_peak_position": "후렴 후반부에 최고음을 배치하는 구조가 안전한 후보",
        "motif_type": infer_motif_type(lyrics_analysis),
        "interval_style": "순차 진행 중심 + 핵심 문장 직전 제한적 도약 추천",
        "singability": "high" if bpm < 120 else "medium",
        "hook_melody_shape": "짧은 상승 후 긴 하행" if bpm < 100 else "짧은 반복 리듬 + 상행 응답",
        "analysis_note": f"{key} 중심의 크로마 추정치를 바탕으로 멜로디 방향을 설계했습니다. MVP는 멜로디 MIDI 추출을 수행하지 않습니다.",
        "creative_principle": "기존 멜로디 라인을 복제하지 말고, 최고음 위치와 반복 모티프 같은 구조적 원리만 새롭게 적용합니다.",
    }


def infer_motif_type(lyrics_analysis: dict) -> str:
    repeated = lyrics_analysis.get("repeated_key_phrases", [])
    if repeated:
        return "반복 가사 문장과 결합되는 짧은 반복 모티프"
    return "제목 후보와 연결되는 2마디 단위 모티프"
