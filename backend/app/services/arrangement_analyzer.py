def analyze_arrangement(metadata: dict, audio_features: dict, structure: dict) -> dict:
    genre = metadata.get("genre") or "Pop"
    brightness = infer_brightness(float(audio_features.get("spectral_centroid_mean", 0)))
    sections = structure.get("structure", [])
    return {
        "main_instruments": infer_instruments(genre),
        "arrangement_build": "gradual layering" if len(sections) >= 4 else "single-section MVP estimate",
        "intro_instruments": "piano/pad or signature texture",
        "verse_instruments": "lead vocal 중심, 저밀도 악기",
        "pre_chorus_instruments": "riser, pad, low strings 후보",
        "chorus_arrangement": "drums, bass, wide harmony layers",
        "bridge_arrangement": "드럼을 줄이고 화성 또는 보컬 메시지를 전면에 배치",
        "final_chorus_lift": "adlibs + backing vocals + cymbal/strings lift",
        "space_design": f"{brightness} 톤을 기준으로 공간계와 고역 레이어를 조절",
        "creative_principle": "악기 추가/제거 타이밍과 에너지 곡선만 참고하고, 특정 리프나 사운드 디자인을 그대로 복제하지 않습니다.",
    }


def infer_instruments(genre: str) -> list[str]:
    if "Ballad" in genre or "발라드" in genre:
        return ["piano", "strings", "bass", "drums", "pad"]
    if "Dance" in genre or "K-pop" in genre:
        return ["drums", "bass", "synth", "vocal chop", "pad"]
    return ["drums", "bass", "keys", "guitar", "synth"]


def infer_brightness(centroid: float) -> str:
    if centroid < 1200:
        return "어둡고 로우미드가 중심인"
    if centroid < 2600:
        return "균형 잡힌"
    return "밝고 선명한"
