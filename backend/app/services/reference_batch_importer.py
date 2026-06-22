from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.db.database import SQLiteStore, make_id
from app.services.curated_reference_catalog import curated_reference_entries
from app.services.hit_song_researcher import build_analysis_from_research_profile, confidence_field
from app.services.report_generator import generate_full_report
from app.services.statistics_service import build_hit_song_statistics


ROOT_DIR = Path(__file__).resolve().parents[3]
QUEUE_PATH = ROOT_DIR / "backend" / "seeds" / "cloud_reference_queue.json"
YOUTUBE_POLICY = (
    "YouTube 링크는 레퍼런스 메타데이터/검색 시작점으로만 사용합니다. "
    "YouTube 오디오는 다운로드, 추출, 분리, 변환, 캡처, 분석하지 않습니다."
)


def import_next_reference_batch(store: SQLiteStore, limit: int = 10) -> dict[str, Any]:
    requested_limit = max(1, min(limit, 10))
    queue = _load_queue()
    selected = _select_unique_candidates(store, queue, requested_limit)
    skipped_duplicate_count = _count_skipped_candidates(store, queue)
    if len(selected) < requested_limit:
        return {
            "requested_limit": requested_limit,
            "imported_count": 0,
            "created_count": 0,
            "skipped_duplicate_count": skipped_duplicate_count,
            "songs": [],
            "total_after": len(store.list_songs()),
            "low_confidence": [],
            "queue_remaining": len(selected),
            "youtube_policy": YOUTUBE_POLICY,
            "message": "신규로 추가할 수 있는 큐 곡이 10곡보다 적습니다. backend/seeds/cloud_reference_queue.json에 실제 히트곡을 더 추가하세요.",
        }

    created: list[dict[str, Any]] = []
    low_confidence: list[str] = []
    for entry in selected:
        profile = _profile_from_queue_entry(entry)
        analysis = _analysis_from_queue_entry(profile, entry)
        song = store.create_song(
            {
                "id": make_id("song"),
                "title": entry["title"],
                "artist": entry["artist"],
                "genre": entry.get("genre"),
                "release_year": entry.get("release_year"),
                "country": entry.get("country"),
                "youtube_url": entry.get("youtube_url"),
                "youtube_metadata": profile["youtube_metadata"],
                "research_profile": profile,
                "duration": None,
                "bpm": entry.get("bpm"),
                "key": entry.get("key"),
                "file_name": None,
            }
        )
        saved_analysis = store.save_analysis(song["id"], analysis)
        created.append({**(store.get_song(song["id"]) or song), "analysis": saved_analysis})
        if str(entry.get("data_confidence") or "").lower() in {"low", "medium-low"}:
            low_confidence.append(f"{entry['title']} - {entry['artist']}: {entry.get('data_confidence')}")

    all_songs = store.list_songs()
    all_analyses = store.get_analyses_for_songs([song["id"] for song in all_songs])
    remaining_after = len(_select_unique_candidates(store, queue, len(queue)))
    return {
        "requested_limit": requested_limit,
        "imported_count": len(created),
        "created_count": len(created),
        "skipped_duplicate_count": skipped_duplicate_count,
        "songs": [_strip_embedded_analysis(song) for song in created],
        "total_after": len(all_songs),
        "low_confidence": low_confidence,
        "queue_remaining": remaining_after,
        "library_statistics": build_hit_song_statistics(all_songs, all_analyses),
        "youtube_policy": YOUTUBE_POLICY,
        "message": f"중복 없이 실제 히트곡 {len(created)}곡을 새로 분석해 누적했습니다.",
    }


def _load_queue() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if QUEUE_PATH.exists():
        entries.extend(json.loads(QUEUE_PATH.read_text(encoding="utf-8")))
    entries.extend(curated_reference_entries())
    return _dedupe_queue(entries)


def _dedupe_queue(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for entry in entries:
        title = entry.get("title")
        artist = entry.get("artist")
        if not title or not artist:
            continue
        key = (title.casefold().strip(), artist.casefold().strip())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


def _select_unique_candidates(store: SQLiteStore, queue: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[str, str]] = set()
    for entry in queue:
        title = entry.get("title")
        artist = entry.get("artist")
        if not title or not artist:
            continue
        key = (title.casefold().strip(), artist.casefold().strip())
        if key in selected_keys:
            continue
        if store.find_song_by_identity(title, artist):
            continue
        selected.append(entry)
        selected_keys.add(key)
        if len(selected) == limit:
            break
    return selected


def _count_skipped_candidates(store: SQLiteStore, queue: list[dict[str, Any]]) -> int:
    skipped = 0
    seen: set[tuple[str, str]] = set()
    for entry in queue:
        title = entry.get("title")
        artist = entry.get("artist")
        if not title or not artist:
            skipped += 1
            continue
        key = (title.casefold().strip(), artist.casefold().strip())
        if key in seen or store.find_song_by_identity(title, artist):
            skipped += 1
            continue
        seen.add(key)
    return skipped


def _profile_from_queue_entry(entry: dict[str, Any]) -> dict[str, Any]:
    confidence = entry.get("data_confidence") or "medium"
    title = entry["title"]
    artist = entry["artist"]
    mood_tags = _infer_mood_tags(entry)
    youtube_url = entry.get("youtube_url")
    return {
        "profile_type": "curated_reference_batch_research",
        "safe_design_policy": {
            "youtube_role": "reference metadata/search starting point only",
            "audio_analysis_source": "none in this batch; future owned-audio modules can be added separately",
            "forbidden": [
                "yt-dlp",
                "youtube-dl",
                "stream ripping",
                "hidden audio capture",
                "YouTube audio separation",
                "downloading YouTube audio to file",
            ],
        },
        "youtube_metadata": {
            "source": "curated reference queue",
            "url": youtube_url,
            "title": f"{artist} - {title}",
            "channel_name": artist,
            "description": "Reference metadata only. No YouTube audio is downloaded, extracted, captured, converted, separated, or analyzed.",
            "thumbnail_url": None,
            "duration": None,
            "published_date": None,
            "view_count": None,
            "metadata_status": "curated_reference",
            "policy": YOUTUBE_POLICY,
        },
        "external_sources": {
            "curated_queue": {
                "status": "available",
                "source": "backend/seeds/cloud_reference_queue.json",
                "notes": "Human-curated public hit-song research fields; no full lyrics and no YouTube audio extraction.",
            }
        },
        "identification": {
            "title": confidence_field(title, "high", "curated reference queue"),
            "artist": confidence_field(artist, "high", "curated reference queue"),
            "release_year": confidence_field(entry.get("release_year"), confidence, "curated reference queue"),
            "genre": confidence_field(entry.get("genre"), confidence, "curated reference queue"),
            "country": confidence_field(entry.get("country"), confidence, "curated reference queue"),
            "video_type": confidence_field("reference search result / official video likely", "low", "metadata not fetched in MVP batch"),
        },
        "musical_features": {
            "bpm": confidence_field(entry.get("bpm"), confidence, "curated public music research"),
            "key": confidence_field(entry.get("key"), confidence, "curated public music research"),
            "popularity_indicators": confidence_field(["well-known domestic/international hit"], "medium", "curated hit-song queue"),
            "mood_tags": confidence_field(mood_tags, confidence, "lyric theme and producer notes inference"),
            "lyric_theme": confidence_field(entry.get("lyric_theme"), confidence, "curated lyric research summary"),
            "hook_type": confidence_field(entry.get("hook_type"), confidence, "curated hook research summary"),
            "structure_notes": confidence_field(entry.get("story_flow"), confidence, "curated story/structure summary"),
            "arrangement_notes": confidence_field(entry.get("arrangement"), confidence, "curated producer research notes"),
            "producer_notes": confidence_field(entry.get("producer_takeaway"), confidence, "curated producer takeaway"),
            "hit_factors": confidence_field([entry.get("hit_factor")], confidence, "curated hit factor research"),
            "lessons_for_new_song_creation": confidence_field([entry.get("producer_takeaway")], confidence, "curated creative principle"),
        },
        "user_inputs": {
            "lyrics_provided": False,
            "chords_provided": bool(entry.get("chord_progression")),
            "notes_provided": True,
            "lyrics_text": None,
            "chord_progression": entry.get("chord_progression"),
            "analysis_notes": entry.get("producer_takeaway"),
        },
        "research_summary": (
            f"{artist}의 '{title}'은 {entry.get('genre') or 'Unknown'} 레퍼런스로 정리됩니다. "
            f"핵심 정서는 {entry.get('lyric_theme') or '추가 확인 필요'}이고, 후크는 {entry.get('hook_type') or '추가 확인 필요'} 중심입니다. "
            "이 프로필은 YouTube 오디오가 아니라 큐레이션된 메타데이터, 공개 음악 연구 정보, 프로듀서 관점 요약을 바탕으로 합니다."
        ),
    }


def _analysis_from_queue_entry(profile: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    analysis = build_analysis_from_research_profile(profile)
    bpm = float(entry.get("bpm") or 0)
    key = entry.get("key") or "Unknown"
    title = entry["title"]
    artist = entry["artist"]
    chord_progression = entry.get("chord_progression")
    confidence = entry.get("data_confidence") or "medium"
    structure = _default_structure(entry)

    analysis["concept"].update(
        {
            "concept": entry.get("lyric_theme"),
            "genre": entry.get("genre"),
            "mood": _infer_mood_tags(entry),
            "sound_image": entry.get("arrangement"),
            "commercial_positioning": "국내외 히트곡 레퍼런스 연구용 큐레이션 데이터",
            "one_sentence_concept": f"{title}은 {entry.get('lyric_theme')}를 {entry.get('hook_type')}로 각인하는 {entry.get('genre')} 레퍼런스입니다.",
        }
    )
    analysis["lyrics"].update(
        {
            "lyrics_provided": False,
            "lyric_theme": entry.get("lyric_theme"),
            "lyric_point_of_view": entry.get("speaker_situation"),
            "speaker": entry.get("speaker_situation"),
            "situation": entry.get("speaker_situation"),
            "story_flow": entry.get("story_flow"),
            "verse_role": "상황과 화자의 감정 출발점을 제시하는 구간으로 연구합니다.",
            "pre_chorus_role": "후렴 전 긴장 또는 감정 압력을 올리는 후보 구간으로 연구합니다.",
            "chorus_role": "제목 단서와 핵심 정서를 짧게 고정하는 구간입니다.",
            "bridge_role": "반복된 감정에 새 시점이나 더 큰 고백을 주는 후보 구간입니다.",
            "title_usage": entry.get("hook_location"),
            "core_message": entry.get("hook_cue"),
            "key_phrase_candidates": [{"line": entry.get("hook_cue"), "score": 1, "reasons": ["short compliant cue only"]}],
            "chorus_key_phrase_type": entry.get("hook_type"),
            "data_confidence": {"lyrics": confidence_field(None, confidence, "curated summary; full lyrics not stored")},
        }
    )
    analysis["structure"].update(
        {
            "structure": structure,
            "structure_notes": entry.get("story_flow"),
            "first_chorus_time": entry.get("first_chorus_time"),
            "final_chorus_expansion": _infer_final_chorus(entry),
            "energy_curve": _energy_curve_for_structure(structure),
            "data_confidence": {"structure": confidence_field(structure, "low", "curated summary without YouTube audio analysis")},
        }
    )
    analysis["harmony"].update(
        {
            "key": key,
            "chorus_progression": chord_progression,
            "verse_progression": analysis["harmony"].get("verse_progression") or chord_progression,
            "creative_principle": "코드 진행 자체를 베끼기보다, 어떤 위치에서 긴장과 해소가 생기는지 일반화해 새 곡에 적용합니다.",
            "data_confidence": {"key": confidence_field(key, confidence, "curated public music research"), "chord_progression": confidence_field(chord_progression, confidence, "curated chord research")},
        }
    )
    analysis["melody"].update(
        {
            "motif_type": entry.get("hook_type"),
            "hook_melody_intervals": entry.get("hook_melody_interval"),
            "hook_melody_rhythm": entry.get("hook_melody_rhythm"),
            "hook_melody_contour": entry.get("hook_melody_interval"),
            "chorus_peak_position": "hook/climax position inferred from reference research",
            "singability": "medium-high",
            "creative_principle": "멜로디 원형을 옮기지 말고, 반복 음/2도/3도/도약 같은 후크 기능만 새 멜로디로 재설계합니다.",
            "data_confidence": {"hook_melody": confidence_field(entry.get("hook_melody_interval"), confidence, "curated interval/rhythm summary; not full transcription")},
        }
    )
    analysis["hook"].update(
        {
            "primary_hook_type": entry.get("hook_type"),
            "hook_location": entry.get("hook_location"),
            "short_hook_cue": entry.get("hook_cue"),
            "why_hook_works": entry.get("why_hook_works"),
            "title_hook_connection": "strong" if entry.get("hook_cue") else "medium",
            "hook_memorability": "high",
            "data_confidence": {"hook": confidence_field(entry.get("hook_type"), confidence, "curated hook research")},
        }
    )
    analysis["rhythm"].update(
        {
            "bpm": bpm,
            "meter": "4/4",
            "groove_type": _groove_for_bpm(bpm),
            "vocal_rhythm": entry.get("hook_melody_rhythm"),
            "verse_chorus_rhythm_contrast": "후렴에서는 제목/후크 리듬을 더 선명하게 반복하는 방향으로 연구합니다.",
        }
    )
    analysis["arrangement"].update(
        {
            "arrangement_build": entry.get("arrangement"),
            "final_chorus_lift": _infer_final_chorus(entry),
            "creative_principle": "악기 조합을 그대로 복제하지 말고, 언제 비우고 언제 확장하는지의 타이밍만 새 곡에 맞게 변형합니다.",
        }
    )
    analysis["vocal"].update(
        {
            "vocal_tone": entry.get("vocal"),
            "chorus_delivery": "hook-focused delivery",
            "creative_principle": "보컬 톤과 에너지 곡선의 역할만 참고하고 원곡 애드리브나 발성 시그니처는 복제하지 않습니다.",
        }
    )
    analysis["mixing"].update(
        {
            "vocal_position": entry.get("mixing"),
            "mastering_loudness_style": "commercial streaming reference",
            "creative_principle": "믹스의 중심 배치와 공간감 원리만 참고하고 사운드 시그니처는 새롭게 만듭니다.",
        }
    )
    analysis["hit_factor"].update(
        {
            "main_hit_factor": entry.get("hit_factor"),
            "why_it_works": entry.get("why_hook_works"),
            "replay_factor": "high",
        }
    )
    analysis["takeaway"].update(
        {
            "transferable_principles": [
                entry.get("producer_takeaway"),
                "후크의 위치, 길이, 리듬 기능만 일반화하고 원곡 멜로디와 가사는 사용하지 않습니다.",
                "여러 곡의 공통 패턴을 통계로 본 뒤 새 곡의 콘셉트에 맞게 변형합니다.",
            ],
            "avoid_copying": [
                entry.get("avoid_copying"),
                "원곡의 멜로디 라인을 그대로 사용하지 않습니다.",
                "원곡 가사 원문이나 긴 구절을 저장하거나 차용하지 않습니다.",
                "식별 가능한 리프, 애드리브, 사운드 시그니처를 복제하지 않습니다.",
            ],
            "recommended_strategy": entry.get("producer_takeaway"),
        }
    )
    analysis["audio_features"].update(
        {
            "bpm": bpm,
            "estimated_key": key,
            "analysis_source": "curated_reference_batch_no_youtube_audio",
        }
    )
    metadata = {
        "title": title,
        "artist": artist,
        "genre": entry.get("genre"),
        "country": entry.get("country"),
        "release_year": entry.get("release_year"),
        "youtube_url": entry.get("youtube_url"),
        "file_name": None,
    }
    analysis["full_report"] = generate_full_report(analysis, metadata, analysis["audio_features"], research_profile=profile)
    return analysis


def _strip_embedded_analysis(song: dict[str, Any]) -> dict[str, Any]:
    result = dict(song)
    result.pop("analysis", None)
    return result


def _infer_mood_tags(entry: dict[str, Any]) -> list[str]:
    theme = str(entry.get("lyric_theme") or "")
    separators = [",", "·", "/", "와", "과"]
    normalized = theme
    for separator in separators:
        normalized = normalized.replace(separator, "|")
    values = [item.strip() for item in normalized.split("|") if item.strip()]
    return values[:4] or ["정서 추가 확인 필요"]


def _default_structure(entry: dict[str, Any]) -> list[str]:
    story = str(entry.get("story_flow") or "")
    if "Bridge" in story or "브리지" in story:
        return ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"]
    return ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Chorus", "Final Chorus"]


def _energy_curve_for_structure(structure: list[str]) -> list[int]:
    values = {
        "Intro": 1,
        "Verse": 3,
        "Pre-Chorus": 5,
        "Chorus": 8,
        "Bridge": 4,
        "Final Chorus": 10,
        "Outro": 2,
    }
    return [values.get(section, 5) for section in structure]


def _infer_final_chorus(entry: dict[str, Any]) -> str:
    arrangement = str(entry.get("arrangement") or "")
    vocal = str(entry.get("vocal") or "")
    if "final" in arrangement.lower() or "final" in vocal.lower() or "마지막" in arrangement or "마지막" in vocal:
        return "final chorus lift with added vocal or arrangement layers"
    if "chorus" in arrangement.lower():
        return "chorus repetition with arrangement density maintained or expanded"
    return "final chorus expansion requires additional score/listening notes"


def _groove_for_bpm(bpm: float) -> str:
    if bpm <= 84:
        return "slow emotional groove"
    if bpm <= 105:
        return "mid-tempo groove"
    if bpm <= 125:
        return "danceable pop groove"
    if bpm <= 145:
        return "up-tempo pop groove"
    return "fast pulse / possible double-time pop feel"
