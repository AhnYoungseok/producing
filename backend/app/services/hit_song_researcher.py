from __future__ import annotations

import re
from typing import Any

from app.services.harmony_analyzer import analyze_harmony
from app.services.lyric_analyzer import analyze_lyrics
from app.services.report_generator import generate_full_report
from app.services.public_music_data_service import collect_public_music_data
from app.services.youtube_metadata_service import collect_youtube_reference_metadata, validate_youtube_reference_url


NOTE_NAMES = {
    -1: "Unknown",
    0: "C",
    1: "C#",
    2: "D",
    3: "D#",
    4: "E",
    5: "F",
    6: "F#",
    7: "G",
    8: "G#",
    9: "A",
    10: "A#",
    11: "B",
}


def build_hit_song_research_profile(
    youtube_url: str,
    lyrics_text: str | None = None,
    chord_progression: str | None = None,
    analysis_notes: str | None = None,
    title_hint: str | None = None,
    artist_hint: str | None = None,
    genre_hint: str | None = None,
    country_hint: str | None = None,
    release_year_hint: int | None = None,
) -> dict[str, Any]:
    normalized_url = validate_youtube_reference_url(youtube_url)
    youtube_metadata = collect_youtube_reference_metadata(normalized_url)
    identification = identify_reference_song(
        youtube_metadata,
        title_hint=title_hint,
        artist_hint=artist_hint,
        genre_hint=genre_hint,
        country_hint=country_hint,
        release_year_hint=release_year_hint,
    )
    public_data = collect_public_music_data(identification["title"]["value"], identification["artist"]["value"])
    return build_structured_profile(
        youtube_metadata=youtube_metadata,
        identification=identification,
        public_data=public_data,
        lyrics_text=lyrics_text,
        chord_progression=chord_progression,
        analysis_notes=analysis_notes,
    )


def identify_reference_song(
    youtube_metadata: dict[str, Any],
    title_hint: str | None = None,
    artist_hint: str | None = None,
    genre_hint: str | None = None,
    country_hint: str | None = None,
    release_year_hint: int | None = None,
) -> dict[str, Any]:
    video_title = youtube_metadata.get("title") or ""
    channel_name = youtube_metadata.get("channel_name")
    parsed_artist, parsed_title = parse_artist_and_title(video_title)
    video_type = classify_video_type(video_title, youtube_metadata.get("description"))
    inferred_year = release_year_hint or infer_release_year(youtube_metadata)
    inferred_genre = genre_hint or infer_genre(video_title, youtube_metadata.get("description"))
    inferred_country = country_hint or infer_country(video_title, channel_name)

    return {
        "title": confidence_field(
            title_hint or parsed_title or video_title or "Untitled Reference",
            "medium" if parsed_title or title_hint else "low",
            "YouTube metadata title parsing",
        ),
        "artist": confidence_field(
            artist_hint or parsed_artist or channel_name,
            "medium" if parsed_artist or artist_hint else "low",
            "YouTube metadata/channel parsing",
        ),
        "release_year": confidence_field(
            inferred_year,
            "medium" if inferred_year else "low",
            "YouTube published date or metadata inference",
        ),
        "genre": confidence_field(
            inferred_genre,
            "medium" if genre_hint else "low",
            "user hint or metadata inference",
        ),
        "country": confidence_field(
            inferred_country,
            "medium" if country_hint else "low",
            "user hint or metadata inference",
        ),
        "video_type": confidence_field(video_type, "medium", "YouTube title and description classification"),
    }


def build_structured_profile(
    youtube_metadata: dict[str, Any],
    identification: dict[str, Any],
    public_data: dict[str, Any],
    lyrics_text: str | None,
    chord_progression: str | None,
    analysis_notes: str | None,
) -> dict[str, Any]:
    enriched_identification = enrich_identification(identification, public_data)
    mood_tags = infer_mood_tags(lyrics_text, analysis_notes, public_data, youtube_metadata)
    lyric_theme = infer_lyric_theme(lyrics_text, youtube_metadata.get("description"), analysis_notes)
    hook_type = infer_hook_type(lyrics_text, analysis_notes, youtube_metadata.get("title"))
    structure_notes = infer_structure_notes(analysis_notes, youtube_metadata)
    arrangement_notes = infer_arrangement_notes(analysis_notes, youtube_metadata)
    hit_factors = infer_hit_factors(youtube_metadata, public_data, hook_type["value"])
    lessons = infer_lessons_for_creation(enriched_identification, hook_type["value"], mood_tags["value"], chord_progression)
    spotify_features = public_data.get("spotify", {}).get("audio_features", {})
    bpm = infer_bpm(spotify_features, analysis_notes)
    key = infer_key(spotify_features, analysis_notes)

    return {
        "profile_type": "youtube_link_hit_song_research",
        "safe_design_policy": {
            "youtube_role": "reference metadata only",
            "audio_analysis_source": "user-uploaded audio only, when provided separately",
            "forbidden": [
                "yt-dlp",
                "youtube-dl",
                "stream ripping",
                "hidden audio capture",
                "YouTube audio separation",
                "downloading YouTube audio to file",
            ],
        },
        "youtube_metadata": youtube_metadata,
        "external_sources": public_data,
        "identification": enriched_identification,
        "musical_features": {
            "bpm": bpm,
            "key": key,
            "popularity_indicators": infer_popularity(public_data, youtube_metadata),
            "mood_tags": mood_tags,
            "lyric_theme": lyric_theme,
            "hook_type": hook_type,
            "structure_notes": structure_notes,
            "arrangement_notes": arrangement_notes,
            "producer_notes": infer_producer_notes(enriched_identification, mood_tags["value"], arrangement_notes["value"]),
            "hit_factors": hit_factors,
            "lessons_for_new_song_creation": lessons,
        },
        "user_inputs": {
            "lyrics_provided": bool(lyrics_text and lyrics_text.strip()),
            "chords_provided": bool(chord_progression and chord_progression.strip()),
            "notes_provided": bool(analysis_notes and analysis_notes.strip()),
            "lyrics_text": lyrics_text,
            "chord_progression": chord_progression,
            "analysis_notes": analysis_notes,
        },
        "research_summary": build_research_summary(enriched_identification, mood_tags["value"], hook_type["value"]),
    }


def build_analysis_from_research_profile(profile: dict[str, Any]) -> dict[str, Any]:
    features = profile["musical_features"]
    identification = profile["identification"]
    bpm_value = features["bpm"]["value"]
    key_value = features["key"]["value"]
    mood_tags = features["mood_tags"]["value"] or []
    hook_type = features["hook_type"]["value"] or "metadata-inferred hook"
    lyrics_text = profile["user_inputs"].get("lyrics_text")
    chord_progression = profile["user_inputs"].get("chord_progression")

    audio_features = {
        "bpm": float(bpm_value) if bpm_value else 0,
        "estimated_key": key_value or "Unknown",
        "duration_seconds": 0,
        "loudness_estimate": 0,
        "onset_density": 0,
        "spectral_centroid_mean": 0,
        "zero_crossing_rate_mean": 0,
        "chroma_summary": {note: 0 for note in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]},
        "analysis_source": "youtube_link_research_profile_no_youtube_audio",
    }
    lyrics_analysis = analyze_lyrics(lyrics_text, identification["title"]["value"])
    harmony_analysis = analyze_harmony(chord_progression, audio_features)
    lyrics_analysis["lyric_theme"] = lyrics_analysis.get("lyric_theme") or features["lyric_theme"]["value"]
    lyrics_analysis.setdefault(
        "data_confidence",
        {
            "lyric_theme": features["lyric_theme"],
            "hook_type": features["hook_type"],
        },
    )
    harmony_analysis.setdefault(
        "data_confidence",
        {
            "key": features["key"],
            "chord_progression": confidence_field(
                chord_progression,
                "medium" if chord_progression else "low",
                "user-provided chords or unavailable",
            ),
        },
    )
    analysis = {
        "concept": {
            "concept": identification["title"]["value"],
            "genre": identification["genre"]["value"],
            "mood": mood_tags,
            "one_sentence_concept": profile["research_summary"],
            "data_confidence": {
                "genre": identification["genre"],
                "mood": features["mood_tags"],
            },
        },
        "lyrics": lyrics_analysis,
        "structure": {
            "structure": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "structure_notes": features["structure_notes"]["value"],
            "first_chorus_time": None,
            "data_confidence": {"structure_notes": features["structure_notes"]},
        },
        "harmony": harmony_analysis,
        "melody": {
            "chorus_peak_position": "requires audio or score; not inferred from YouTube audio",
            "creative_principle": "Use reference-level melody principles only; do not copy melody lines.",
            "data_confidence": {
                "chorus_peak_position": confidence_field(None, "low", "not available without score/audio owned by user"),
            },
        },
        "hook": {
            "primary_hook_type": hook_type,
            "hook_memorability": "research estimate",
            "data_confidence": {"primary_hook_type": features["hook_type"]},
        },
        "rhythm": {
            "bpm": bpm_value,
            "groove_type": "requires structured API or user audio",
            "data_confidence": {"bpm": features["bpm"]},
        },
        "arrangement": {
            "arrangement_build": features["arrangement_notes"]["value"],
            "creative_principle": "Generalize arrangement roles and energy curve; do not copy identifiable riffs.",
            "data_confidence": {"arrangement_notes": features["arrangement_notes"]},
        },
        "vocal": {
            "vocal_tone": "metadata/user-note inference",
            "creative_principle": "Infer vocal role from context; confirm by listening only to lawful sources.",
            "data_confidence": {"producer_notes": features["producer_notes"]},
        },
        "mixing": {
            "vocal_position": "not available from metadata",
            "creative_principle": "Mixing claims are low-confidence unless user supplies notes or owned audio.",
            "data_confidence": {"mixing": confidence_field(None, "low", "metadata cannot measure mix position")},
        },
        "hit_factor": {
            "main_hit_factor": ", ".join(features["hit_factors"]["value"][:3]) if features["hit_factors"]["value"] else "research pending",
            "replay_factor": "estimated from popularity context and hook inference",
            "data_confidence": {"hit_factors": features["hit_factors"]},
        },
        "takeaway": {
            "transferable_principles": features["lessons_for_new_song_creation"]["value"],
            "avoid_copying": [
                "Do not reuse the original melody line.",
                "Do not reuse the original lyrics.",
                "Do not copy an identifiable arrangement riff or sound signature.",
            ],
            "data_confidence": {"lessons": features["lessons_for_new_song_creation"]},
        },
        "audio_features": audio_features,
    }
    metadata = {
        "title": identification["title"]["value"],
        "artist": identification["artist"]["value"],
        "genre": identification["genre"]["value"],
        "country": identification["country"]["value"],
        "release_year": identification["release_year"]["value"],
        "youtube_url": profile["youtube_metadata"].get("url"),
        "file_name": None,
    }
    analysis["full_report"] = generate_full_report(analysis, metadata, audio_features, research_profile=profile)
    analysis["full_report"]["research_profile"] = profile
    return analysis


def enrich_identification(identification: dict[str, Any], public_data: dict[str, Any]) -> dict[str, Any]:
    result = dict(identification)
    spotify = public_data.get("spotify", {})
    musicbrainz = public_data.get("musicbrainz", {})
    lastfm = public_data.get("lastfm", {})

    if spotify.get("status") == "available":
        _replace_if_better(result, "title", spotify.get("title"), "high", "Spotify track search")
        _replace_if_better(result, "artist", spotify.get("artist"), "high", "Spotify track search")
        _replace_if_better(result, "release_year", spotify.get("release_year"), "high", "Spotify album release date")
    elif musicbrainz.get("status") == "available":
        _replace_if_better(result, "title", musicbrainz.get("title"), "high", "MusicBrainz recording search")
        _replace_if_better(result, "artist", musicbrainz.get("artist"), "high", "MusicBrainz artist credit")
        _replace_if_better(result, "release_year", musicbrainz.get("release_year"), "high", "MusicBrainz first release date")

    tags = []
    tags.extend(musicbrainz.get("tags", []) if musicbrainz.get("status") == "available" else [])
    tags.extend(lastfm.get("tags", []) if lastfm.get("status") == "available" else [])
    if tags and result["genre"]["confidence"] == "low":
        result["genre"] = confidence_field(tags[0], "medium", "MusicBrainz/Last.fm tags")

    return result


def parse_artist_and_title(video_title: str) -> tuple[str | None, str | None]:
    cleaned = clean_video_title(video_title)
    for separator in [" - ", " – ", " — ", " | ", "｜"]:
        if separator in cleaned:
            artist, title = cleaned.split(separator, 1)
            return artist.strip() or None, title.strip() or None
    return None, cleaned.strip() or None


def clean_video_title(title: str) -> str:
    cleaned = re.sub(
        r"\[[^\]]+\]|\([^\)]*(official|mv|m/v|music video|lyrics?|audio|live|cover|fan|remaster|4k)[^\)]*\)",
        "",
        title,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" -|")


def classify_video_type(title: str, description: str | None) -> str:
    text = f"{title} {description or ''}".lower()
    if re.search(r"\bcover\b", text):
        return "cover"
    if re.search(r"\blyric", text):
        return "lyric video"
    if re.search(r"\blive\b", text):
        return "live"
    if "official" in text and ("mv" in text or "m/v" in text or "music video" in text or "video" in text):
        return "official MV"
    if re.search(r"\bfan\b", text):
        return "fan upload"
    return "reference video"


def infer_release_year(youtube_metadata: dict[str, Any]) -> int | None:
    for value in [youtube_metadata.get("published_date"), youtube_metadata.get("description"), youtube_metadata.get("title")]:
        if not value:
            continue
        match = re.search(r"(19|20)\d{2}", str(value))
        if match:
            return int(match.group(0))
    return None


def infer_genre(title: str, description: str | None) -> str | None:
    text = normalize_text(f"{title} {description or ''}")
    has_ballad = contains_any(text, ["ballad", "발라드"])
    has_kpop = contains_any(text, ["k-pop", "kpop", "korean pop", "케이팝"])

    if has_kpop and has_ballad:
        return "K-pop Ballad"
    if has_ballad:
        return "Pop Ballad"
    if has_kpop:
        return "K-pop"
    if re.search(r"\b(r&b|rnb)\b", text):
        return "R&B"
    if re.search(r"\b(hip hop|hip-hop|rap)\b", text):
        return "Hip-hop"
    if re.search(r"\brock\b", text):
        return "Rock"
    if re.search(r"\b(dance|edm)\b", text):
        return "Dance Pop"
    return None


def infer_country(title: str, channel_name: str | None) -> str | None:
    text = normalize_text(f"{title} {channel_name or ''}")
    if contains_any(text, ["k-pop", "kpop", "korea", "korean", "한국", "케이팝"]):
        return "KR"
    if contains_any(text, ["j-pop", "jpop", "japan", "japanese", "일본"]):
        return "JP"
    return None


def infer_bpm(spotify_features: dict[str, Any], analysis_notes: str | None) -> dict[str, Any]:
    if spotify_features.get("tempo"):
        return confidence_field(round(float(spotify_features["tempo"]), 2), "high", "Spotify structured audio features")
    bpm_from_notes = infer_bpm_from_text(analysis_notes)
    if bpm_from_notes:
        return confidence_field(bpm_from_notes, "low", "user notes text inference")
    return confidence_field(None, "low", "unavailable without structured API or user-owned audio")


def infer_key(spotify_features: dict[str, Any], analysis_notes: str | None) -> dict[str, Any]:
    if spotify_features.get("key") is not None:
        note = NOTE_NAMES.get(int(spotify_features["key"]), "Unknown")
        mode = "major" if spotify_features.get("mode") == 1 else "minor" if spotify_features.get("mode") == 0 else ""
        return confidence_field(f"{note} {mode}".strip(), "high", "Spotify structured audio features")
    text_key = infer_key_from_text(analysis_notes)
    if text_key:
        return confidence_field(text_key, "low", "user notes text inference")
    return confidence_field(None, "low", "unavailable without structured API or user-owned audio")


def infer_popularity(public_data: dict[str, Any], youtube_metadata: dict[str, Any]) -> dict[str, Any]:
    spotify = public_data.get("spotify", {})
    lastfm = public_data.get("lastfm", {})
    value = {
        "spotify_popularity": spotify.get("popularity") if spotify.get("status") == "available" else None,
        "lastfm_listeners": lastfm.get("listeners") if lastfm.get("status") == "available" else None,
        "lastfm_playcount": lastfm.get("playcount") if lastfm.get("status") == "available" else None,
        "youtube_view_count": youtube_metadata.get("view_count"),
    }
    if any(item is not None for item in value.values()):
        return confidence_field(value, "medium", "public metadata and configured music APIs")
    return confidence_field(value, "low", "limited public metadata")


def infer_mood_tags(
    lyrics_text: str | None,
    analysis_notes: str | None,
    public_data: dict[str, Any],
    youtube_metadata: dict[str, Any],
) -> dict[str, Any]:
    tags = []
    for source_name in ["lastfm", "musicbrainz"]:
        source = public_data.get(source_name, {})
        if source.get("status") == "available":
            tags.extend(source.get("tags", []))

    text = normalize_text(f"{lyrics_text or ''} {analysis_notes or ''} {youtube_metadata.get('description') or ''}")
    mood_rules = {
        "그리움": ["miss", "missing", "그리움", "그립", "보고 싶"],
        "사랑": ["love", "사랑"],
        "위로": ["comfort", "heal", "위로", "괜찮"],
        "희망": ["hope", "dream", "희망", "꿈"],
        "슬픔": ["sad", "cry", "슬픔", "눈물", "이별"],
        "에너지": ["dance", "party", "energy", "신나는"],
    }
    for mood, needles in mood_rules.items():
        if contains_any(text, needles):
            tags.append(mood)

    unique_tags = list(dict.fromkeys(tags))[:8]
    confidence = "medium" if public_data.get("lastfm", {}).get("status") == "available" or lyrics_text or analysis_notes else "low"
    return confidence_field(unique_tags, confidence, "Last.fm/MusicBrainz tags, user lyrics, metadata inference")


def infer_lyric_theme(lyrics_text: str | None, description: str | None, analysis_notes: str | None) -> dict[str, Any]:
    text = normalize_text(f"{lyrics_text or ''} {description or ''} {analysis_notes or ''}")
    if not text.strip():
        return confidence_field("가사 정보 없음", "low", "no lyrics provided")

    themes = [
        ("이별과 그리움", ["miss", "missing", "goodbye", "farewell", "이별", "그리움", "보고 싶"]),
        ("사랑 고백", ["love", "forever", "always", "사랑", "고백"]),
        ("자기 확신과 성장", ["dream", "rise", "strong", "성장", "꿈", "해낼"]),
        ("위로와 회복", ["comfort", "heal", "괜찮", "위로", "회복"]),
        ("파티와 해방감", ["party", "dance", "tonight", "파티", "춤"]),
    ]
    for theme, needles in themes:
        if contains_any(text, needles):
            return confidence_field(theme, "medium" if lyrics_text or analysis_notes else "low", "user lyrics or metadata theme inference")
    return confidence_field("일반적인 팝 정서", "low", "metadata text inference")


def infer_hook_type(lyrics_text: str | None, analysis_notes: str | None, video_title: str | None) -> dict[str, Any]:
    text = normalize_text(f"{lyrics_text or ''} {analysis_notes or ''} {video_title or ''}")
    if contains_any(text, ["repeat", "repeated", "반복", "title", "제목", "lyric hook", "가사 후크"]):
        return confidence_field("title / lyric hook", "medium" if lyrics_text or analysis_notes else "low", "lyrics/notes/title inference")
    if contains_any(text, ["riff", "drop", "beat", "sound hook", "리프", "드롭", "비트"]):
        return confidence_field("sound / rhythm hook", "low", "notes/title inference")
    return confidence_field("lyric + melody hook", "low", "default hit-song research heuristic")


def infer_structure_notes(analysis_notes: str | None, youtube_metadata: dict[str, Any]) -> dict[str, Any]:
    if analysis_notes:
        return confidence_field(analysis_notes[:400], "medium", "user-provided notes")
    metadata_status = youtube_metadata.get("metadata_status")
    return confidence_field(
        f"YouTube 메타데이터만으로 곡 구조를 확정할 수 없습니다. 악보, 사용자 메모, 권리 보유 오디오가 있으면 더 정확해집니다. Metadata status: {metadata_status}.",
        "low",
        "metadata-only limitation",
    )


def infer_arrangement_notes(analysis_notes: str | None, youtube_metadata: dict[str, Any]) -> dict[str, Any]:
    text = normalize_text(f"{analysis_notes or ''} {youtube_metadata.get('description') or ''}")
    if contains_any(text, ["piano", "피아노", "ballad", "발라드"]):
        return confidence_field("피아노 또는 보컬 중심의 편곡일 가능성이 있습니다. 실제 확인은 합법적인 청취나 사용자 메모가 필요합니다.", "low", "metadata and notes inference")
    if contains_any(text, ["guitar", "기타", "acoustic"]):
        return confidence_field("기타 중심의 친밀한 편곡일 가능성이 있습니다. 구체적 리프는 복제하지 않고 역할만 참고해야 합니다.", "low", "metadata and notes inference")
    if contains_any(text, ["dance", "edm", "synth", "신스"]):
        return confidence_field("리듬과 신스 레이어가 중심인 편곡일 가능성이 있습니다. 에너지 설계 원리만 참고하세요.", "low", "metadata and notes inference")
    return confidence_field("편곡 정보는 사용자 메모, 크레딧, 권리 보유 오디오가 있어야 신뢰도를 높일 수 있습니다.", "low", "metadata-only limitation")


def infer_producer_notes(identification: dict[str, Any], mood_tags: list[str], arrangement_notes: str | None) -> dict[str, Any]:
    genre = identification["genre"]["value"] or "장르 미확정"
    mood_text = ", ".join(mood_tags) if mood_tags else "정서 미확정"
    return confidence_field(
        f"이 레퍼런스는 {genre} 맥락에서 {mood_text}를 다루는 곡으로 우선 정리할 수 있습니다. 편곡 메모는 사운드를 베끼는 용도가 아니라 에너지 배치와 역할 설계의 힌트로만 사용하세요. {arrangement_notes or ''}",
        "low",
        "AI reasoning over metadata and user inputs",
    )


def infer_hit_factors(youtube_metadata: dict[str, Any], public_data: dict[str, Any], hook_type: str | None) -> dict[str, Any]:
    factors = []
    if hook_type:
        factors.append(f"clear {hook_type}")
    if youtube_metadata.get("view_count"):
        factors.append("visible YouTube popularity signal")
    if public_data.get("spotify", {}).get("popularity") is not None:
        factors.append("Spotify popularity context")
    if public_data.get("lastfm", {}).get("listeners") is not None:
        factors.append("Last.fm listener context")
    if not factors:
        factors.append("requires more public data or user notes")
    confidence = "medium" if len(factors) > 1 else "low"
    return confidence_field(factors, confidence, "public popularity metadata and AI reasoning")


def infer_lessons_for_creation(
    identification: dict[str, Any],
    hook_type: str | None,
    mood_tags: list[str],
    chord_progression: str | None,
) -> dict[str, Any]:
    lessons = [
        "원곡의 멜로디나 가사를 가져오지 말고, 감정 기능과 구조적 역할만 추출하세요.",
        f"후렴은 새로운 문장과 멜로디로 설계하되, 참고 후크 유형은 {hook_type or '미확정'}입니다.",
        "한 곡만 기준으로 삼지 말고 여러 레퍼런스의 공통 패턴을 모아 일반화하세요.",
    ]
    if mood_tags:
        lessons.append(f"새 곡의 정서는 이 팔레트를 참고하되 독자적으로 재구성하세요: {', '.join(mood_tags[:3])}.")
    if chord_progression:
        lessons.append("입력한 코드 진행은 사용자 제공 정보로 저장하고, 후렴 시작 화음을 바꿔 긴장과 해소를 비교해 보세요.")
    return confidence_field(lessons, "medium", "AI reasoning over profile, user inputs, and metadata")


def build_research_summary(identification: dict[str, Any], mood_tags: list[str], hook_type: str | None) -> str:
    title = identification["title"]["value"] or "레퍼런스"
    artist = identification["artist"]["value"] or "unknown artist"
    genre = identification["genre"]["value"] or "장르 미확정"
    mood_text = ", ".join(mood_tags[:3]) if mood_tags else "아직 확정되지 않은 정서"
    hook_text = hook_type or "추가 확인이 필요한 후크"

    return (
        f"{artist}의 '{title}'은 {genre} 레퍼런스로 정리됩니다. "
        f"현재 데이터상 핵심 정서는 {mood_text}이며, 후크는 {hook_text} 방향으로 추정됩니다. "
        "이 프로필은 YouTube 오디오를 분석하지 않고, 허용된 메타데이터와 공개 음악 데이터, 사용자 입력을 바탕으로 "
        "창작 원리를 일반화합니다."
    )


def infer_bpm_from_text(text: str | None) -> float | None:
    if not text:
        return None
    match = re.search(r"(\d{2,3}(?:\.\d+)?)\s*bpm", text, flags=re.IGNORECASE)
    return float(match.group(1)) if match else None


def infer_key_from_text(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"\b([A-G](?:#|b)?\s*(?:major|minor|maj|min)?)\b", text, flags=re.IGNORECASE)
    return match.group(1) if match else None


def confidence_field(value: Any, confidence: str, source: str, notes: str | None = None) -> dict[str, Any]:
    return {
        "value": value,
        "confidence": confidence,
        "source": source,
        "notes": notes,
    }


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def contains_any(text: str, needles: list[str]) -> bool:
    return any(needle.lower() in text for needle in needles)


def _replace_if_better(target: dict[str, Any], key: str, value: Any, confidence: str, source: str) -> None:
    if value:
        target[key] = confidence_field(value, confidence, source)
