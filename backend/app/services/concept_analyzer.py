def analyze_concept(metadata: dict, audio_features: dict, lyrics_text: str | None) -> dict:
    genre = metadata.get("genre") or infer_genre(audio_features)
    mood = infer_mood(audio_features, lyrics_text)
    theme = infer_theme(lyrics_text, metadata.get("analysis_notes"))
    concept = f"{', '.join(mood[:2])} 정서를 중심으로 한 {genre} 레퍼런스"
    return {
        "concept": concept,
        "genre": genre,
        "mood": mood,
        "target_listener": infer_target_listener(genre, metadata.get("country")),
        "theme": theme,
        "era_sound": infer_era_sound(metadata.get("release_year")),
        "artist_image_relation": "아티스트 이미지 정보는 MVP에서 사용자가 입력한 메타데이터와 곡의 정서로 추정합니다.",
        "one_sentence_concept": f"{theme}라는 주제를 {mood[0]} 톤으로 풀어내는 {genre} 곡",
        "creative_principle": "콘셉트는 특정 곡의 외형을 복제하지 말고, 감정의 초점과 청자 경험을 일반화해서 새 곡에 적용해야 합니다.",
    }


def infer_genre(audio_features: dict) -> str:
    bpm = float(audio_features.get("bpm", 0))
    if bpm < 80:
        return "Ballad"
    if bpm < 115:
        return "Midtempo Pop"
    if bpm < 145:
        return "Pop Dance"
    return "High-energy Pop"


def infer_mood(audio_features: dict, lyrics_text: str | None) -> list[str]:
    text = (lyrics_text or "").lower()
    if any(word in text for word in ["이별", "그리움", "miss", "alone", "밤"]):
        return ["그리움", "회상", "절제"]
    if any(word in text for word in ["love", "사랑", "설렘"]):
        return ["설렘", "따뜻함", "기대"]
    loudness = float(audio_features.get("loudness_estimate", -20))
    onset = float(audio_features.get("onset_density", 0))
    if loudness > -14 and onset > 3:
        return ["에너지", "해방감", "직진성"]
    return ["담담함", "집중", "서사"]


def infer_theme(lyrics_text: str | None, analysis_notes: str | None = None) -> str:
    text = f"{lyrics_text or ''} {analysis_notes or ''}"
    if "이별" in text or "그리움" in text:
        return "이별 이후의 감정 정리"
    if "사랑" in text:
        return "사랑의 발견과 고백"
    if "꿈" in text or "성장" in text:
        return "성장과 자기 확신"
    return "사용자가 입력한 메타데이터를 바탕으로 한 정서 중심 콘셉트"


def infer_target_listener(genre: str, country: str | None) -> str:
    region = country or "글로벌"
    if "Ballad" in genre:
        return f"{region} 감성 발라드와 보컬 중심 음악을 선호하는 청자"
    return f"{region} 팝/대중음악 청자"


def infer_era_sound(release_year: int | None) -> str:
    if not release_year:
        return "발매 연도 정보가 없어 현대 스트리밍 환경 기준으로 해석"
    if release_year < 2000:
        return "아날로그 질감과 긴 호흡의 편곡이 중심이던 시대"
    if release_year < 2015:
        return "디지털 팝 프로덕션과 라디오 친화적 구성이 강한 시대"
    return "스트리밍, 숏폼, 장르 융합을 함께 고려하는 현대적 사운드"
