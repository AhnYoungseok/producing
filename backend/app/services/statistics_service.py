from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any, Iterable


def build_hit_song_statistics(songs: list[dict[str, Any]], analyses: list[dict[str, Any]]) -> dict[str, Any]:
    analysis_by_song_id = {analysis["song_id"]: analysis for analysis in analyses}
    analyzed_songs = [song for song in songs if song.get("id") in analysis_by_song_id]
    bpms = [float(song["bpm"]) for song in analyzed_songs if song.get("bpm") is not None]
    first_chorus_times = [
        float(analysis.get("structure", {}).get("first_chorus_time"))
        for analysis in analyses
        if analysis.get("structure", {}).get("first_chorus_time") is not None
    ]

    mood_values = _collect_moods(analyses)
    lyric_themes = [analysis.get("lyrics", {}).get("lyric_theme") for analysis in analyses]
    structures = [" - ".join(_as_list(analysis.get("structure", {}).get("structure"))) for analysis in analyses]
    verse_progressions = [_meaningful_progression(analysis.get("harmony", {}).get("verse_progression")) for analysis in analyses]
    pre_chorus_progressions = [_meaningful_progression(analysis.get("harmony", {}).get("pre_chorus_progression")) for analysis in analyses]
    chorus_progressions = [_meaningful_progression(analysis.get("harmony", {}).get("chorus_progression")) for analysis in analyses]
    bridge_progressions = [_meaningful_progression(analysis.get("harmony", {}).get("bridge_progression")) for analysis in analyses]
    hook_types = [analysis.get("hook", {}).get("primary_hook_type") for analysis in analyses]
    title_usage = [analysis.get("lyrics", {}).get("title_usage") for analysis in analyses]
    final_chorus_expansions = [_final_chorus_expansion(analysis) for analysis in analyses]
    arrangement_features = _collect_arrangement_features(analyses)
    vocal_treatments = _collect_vocal_treatments(analyses)
    hit_factors = _collect_hit_factors(analyses)
    transferable_principles = _collect_transferable_principles(analyses)
    title_in_chorus_count = sum(1 for value in title_usage if _mentions_chorus(value))

    by_genre = _counts(song.get("genre") or "Unknown" for song in analyzed_songs)
    by_country = _counts(song.get("country") or "Unknown" for song in analyzed_songs)
    by_decade = _counts(_decade(song.get("release_year")) for song in analyzed_songs)
    bpm_distribution = _counts(_bpm_bucket(song.get("bpm")) for song in analyzed_songs)
    top_keys = _counts(song.get("key") for song in analyzed_songs)
    top_verse_progressions = _counts(verse_progressions)
    top_pre_chorus_progressions = _counts(pre_chorus_progressions)
    top_chorus_progressions = _counts(chorus_progressions)
    top_bridge_progressions = _counts(bridge_progressions)
    top_song_structures = _counts(structures)
    hook_type_distribution = _counts(hook_types)
    title_usage_distribution = _counts(title_usage)
    chorus_peak_positions = _counts(analysis.get("melody", {}).get("chorus_peak_position") for analysis in analyses)
    top_final_chorus_expansions = _counts(final_chorus_expansions)
    arrangement_builds = _counts(analysis.get("arrangement", {}).get("arrangement_build") for analysis in analyses)
    top_mood_keywords = _counts(mood_values)
    top_lyric_themes = _counts(lyric_themes)
    top_arrangement_features = _counts(arrangement_features)
    top_vocal_treatments = _counts(vocal_treatments)
    top_hit_factors = _counts(hit_factors)
    top_transferable_principles = _counts(transferable_principles)
    title_in_chorus_ratio = round(title_in_chorus_count / len(title_usage), 3) if title_usage else 0

    stats = {
        "summary": {
            "song_count": len(songs),
            "analyzed_song_count": len(analyzed_songs),
            "average_bpm": round(mean(bpms), 2) if bpms else 0,
            "average_first_chorus_time": round(mean(first_chorus_times), 2) if first_chorus_times else None,
            "title_in_chorus_ratio": title_in_chorus_ratio,
        },
        "by_genre": by_genre,
        "by_country": by_country,
        "by_decade": by_decade,
        "by_bpm_range": bpm_distribution,
        "bpm_distribution": bpm_distribution,
        "by_mood": top_mood_keywords,
        "average_bpm_by_genre": _average_bpm_by(songs=analyzed_songs, group_key="genre"),
        "top_keys": top_keys,
        "top_verse_progressions": top_verse_progressions,
        "top_pre_chorus_progressions": top_pre_chorus_progressions,
        "top_chorus_progressions": top_chorus_progressions,
        "top_bridge_progressions": top_bridge_progressions,
        "top_song_structures": top_song_structures,
        "top_structures": top_song_structures,
        "hook_type_distribution": hook_type_distribution,
        "title_usage_distribution": title_usage_distribution,
        "title_in_chorus_ratio": title_in_chorus_ratio,
        "chorus_peak_positions": chorus_peak_positions,
        "final_chorus_expansions": top_final_chorus_expansions,
        "top_final_chorus_expansions": top_final_chorus_expansions,
        "arrangement_builds": arrangement_builds,
        "top_mood_keywords": top_mood_keywords,
        "top_lyric_themes": top_lyric_themes,
        "top_arrangement_features": top_arrangement_features,
        "top_vocal_treatments": top_vocal_treatments,
        "top_hit_factors": top_hit_factors,
        "top_transferable_principles": top_transferable_principles,
        "common_principles_top_10": top_transferable_principles,
        "chart_datasets": _build_chart_datasets(
            by_genre=by_genre,
            by_country=by_country,
            by_decade=by_decade,
            bpm_distribution=bpm_distribution,
            top_keys=top_keys,
            top_verse_progressions=top_verse_progressions,
            top_pre_chorus_progressions=top_pre_chorus_progressions,
            top_chorus_progressions=top_chorus_progressions,
            top_bridge_progressions=top_bridge_progressions,
            top_song_structures=top_song_structures,
            hook_type_distribution=hook_type_distribution,
            title_usage_distribution=title_usage_distribution,
            chorus_peak_positions=chorus_peak_positions,
            top_final_chorus_expansions=top_final_chorus_expansions,
            top_mood_keywords=top_mood_keywords,
            top_lyric_themes=top_lyric_themes,
            top_arrangement_features=top_arrangement_features,
            top_vocal_treatments=top_vocal_treatments,
            top_hit_factors=top_hit_factors,
            top_transferable_principles=top_transferable_principles,
        ),
        "pattern_summaries": _build_pattern_summaries(
            bpms=bpms,
            first_chorus_times=first_chorus_times,
            top_chorus_progressions=top_chorus_progressions,
            hook_type_distribution=hook_type_distribution,
            top_song_structures=top_song_structures,
            top_arrangement_features=top_arrangement_features,
            top_vocal_treatments=top_vocal_treatments,
            top_hit_factors=top_hit_factors,
            top_transferable_principles=top_transferable_principles,
        ),
        "feature_schema": reference_song_feature_schema(),
        "composer_questions": _composer_question_cards(analyzed_songs, analyses, bpms, first_chorus_times),
    }
    return stats


def reference_song_feature_schema() -> list[dict[str, Any]]:
    return [
        {
            "category": "Reference Metadata",
            "fields": [
                "title",
                "artist",
                "genre",
                "country",
                "release_year",
                "youtube_url",
                "video_type",
                "published_date",
                "view_count",
            ],
        },
        {
            "category": "Chord and Structure Analysis",
            "fields": [
                "bpm",
                "key",
                "verse_progression",
                "pre_chorus_progression",
                "chorus_progression",
                "bridge_progression",
                "song_structure",
                "first_chorus_time",
                "final_chorus_expansion",
            ],
        },
        {
            "category": "Hook and Melody Research",
            "fields": [
                "hook_type",
                "hook_location",
                "hook_repeat_count",
                "title_hook_connection",
                "chorus_peak_position",
                "motif_type",
                "singability",
            ],
        },
        {
            "category": "Producer Research Mode",
            "fields": [
                "lyric_theme",
                "mood_tags",
                "arrangement_features",
                "vocal_production_features",
                "mixing_features",
                "hit_factors",
                "transferable_principles",
                "avoid_copying",
                "data_confidence",
            ],
        },
    ]


def _build_chart_datasets(**datasets: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    labels = {
        "by_genre": ("장르별 레퍼런스 수", "YouTube Reference Analysis DB에 쌓인 곡의 장르 분포입니다."),
        "by_country": ("국가별 레퍼런스 수", "국가/시장 기준으로 레퍼런스가 얼마나 쌓였는지 봅니다."),
        "by_decade": ("시대별 레퍼런스 수", "발매 연도 기준으로 시대별 연구 데이터 균형을 확인합니다."),
        "bpm_distribution": ("BPM 분포", "Reference Song Analysis에서 가장 많이 보이는 템포 구간입니다."),
        "top_keys": ("Key 분포", "Chord and Structure Analysis에서 자주 등장하는 조성입니다."),
        "top_verse_progressions": ("Verse 코드 진행 Top 10", "사용자가 입력한 Verse 진행만 모아 집계합니다."),
        "top_pre_chorus_progressions": ("Pre-Chorus 코드 진행 Top 10", "후렴 직전 긴장을 만드는 코드 진행을 집계합니다."),
        "top_chorus_progressions": ("후렴 코드 진행 Top 10", "사용자 입력과 공개 데이터 기반으로 저장된 후렴 진행입니다."),
        "top_bridge_progressions": ("Bridge 코드 진행 Top 10", "전환부와 마지막 후렴 리프트 전의 코드 진행을 집계합니다."),
        "top_song_structures": ("곡 구조 Top 10", "Intro, Verse, Pre, Chorus, Bridge, Final Chorus 흐름의 분포입니다."),
        "hook_type_distribution": ("후크 유형 분포", "가사 후크, 멜로디 후크, 리듬 후크 등 기억 장치의 분포입니다."),
        "title_usage_distribution": ("제목 사용 위치", "제목이 가사와 후렴에서 어떻게 쓰이는지 추적합니다."),
        "chorus_peak_positions": ("후렴 최고음 위치", "후렴 멜로디가 어느 지점에서 감정적으로 상승하는지 봅니다."),
        "top_final_chorus_expansions": ("마지막 후렴 확장 방식", "Final Chorus에서 자주 쓰이는 리프트 전략입니다."),
        "top_mood_keywords": ("감정 키워드 Top 10", "곡의 정서 팔레트 분포입니다."),
        "top_lyric_themes": ("가사 주제 Top 10", "가사 스토리텔링의 주제 분포입니다."),
        "top_arrangement_features": ("편곡 특징 Top 10", "레이어링, 악기, 공간 설계의 반복 패턴입니다."),
        "top_vocal_treatments": ("보컬 프로덕션 Top 10", "보컬 톤, 더블링, 하모니, 애드리브 등 처리 방식입니다."),
        "top_hit_factors": ("히트 포인트 Top 10", "곡이 기억되는 요소를 일반화한 항목입니다."),
        "top_transferable_principles": ("창작 적용 원리 Top 10", "원곡 복제가 아니라 새 곡에 적용할 수 있는 공통 원리입니다."),
    }
    chart_data = {}
    for key, items in datasets.items():
        title, description = labels[key]
        chart_data[key] = {
            "id": key,
            "title": title,
            "description": description,
            "type": "horizontal_bar",
            "items": items,
            "insight": _chart_insight(title, items),
        }
    return chart_data


def _build_pattern_summaries(
    bpms: list[float],
    first_chorus_times: list[float],
    top_chorus_progressions: list[dict[str, Any]],
    hook_type_distribution: list[dict[str, Any]],
    top_song_structures: list[dict[str, Any]],
    top_arrangement_features: list[dict[str, Any]],
    top_vocal_treatments: list[dict[str, Any]],
    top_hit_factors: list[dict[str, Any]],
    top_transferable_principles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "id": "tempo_center",
            "title": "Tempo Center",
            "summary": f"현재 레퍼런스 평균 BPM은 약 {round(mean(bpms), 1)}입니다." if bpms else "BPM 데이터가 더 필요합니다.",
            "producer_takeaway": "목표 장르를 정한 뒤 평균 BPM 주변에서 보컬 호흡과 리듬 밀도를 먼저 설계하세요.",
            "confidence": "medium" if len(bpms) >= 5 else "low",
        },
        {
            "id": "chorus_entry",
            "title": "Chorus Entry Timing",
            "summary": f"첫 후렴은 평균 {round(mean(first_chorus_times), 1)}초 부근에 등장합니다." if first_chorus_times else "첫 후렴 시점 데이터가 부족합니다.",
            "producer_takeaway": "스트리밍 친화적인 곡은 첫 후렴 전까지 제목, 리듬, 사운드 후크 중 하나를 미리 제시하는 편이 좋습니다.",
            "confidence": "medium" if len(first_chorus_times) >= 5 else "low",
        },
        _summary_from_counts(
            "chorus_harmony",
            "Chorus Harmony Pattern",
            top_chorus_progressions,
            "후렴 코드 진행은 {label} 경향이 가장 많이 보입니다.",
            "진행을 그대로 쓰기보다 후렴 첫 마디의 긴장/해소 역할을 새 멜로디에 맞게 변형하세요.",
        ),
        _summary_from_counts(
            "hook_design",
            "Hook Design Pattern",
            hook_type_distribution,
            "후크 유형은 {label} 경향이 가장 많이 보입니다.",
            "후렴 첫 두 마디에서 제목형 문장, 반복 리듬, 짧은 모티브 중 하나를 중심 장치로 정하세요.",
        ),
        _summary_from_counts(
            "song_structure",
            "Song Structure Pattern",
            top_song_structures,
            "곡 구조는 {label} 흐름이 가장 많이 보입니다.",
            "구조는 참고하되 각 파트의 길이와 에너지 차이는 새 곡의 컨셉에 맞게 다시 설계하세요.",
        ),
        _summary_from_counts(
            "arrangement",
            "Arrangement Pattern",
            top_arrangement_features,
            "편곡 특징은 {label} 경향이 가장 많이 보입니다.",
            "특정 리프를 복제하지 말고 악기 추가/제거 타이밍과 마지막 후렴 리프트 원리만 참고하세요.",
        ),
        _summary_from_counts(
            "vocal_production",
            "Vocal Production Pattern",
            top_vocal_treatments,
            "보컬 처리에서는 {label} 특징이 자주 보입니다.",
            "Verse와 Chorus의 보컬 거리감 차이를 먼저 설계하고, 마지막 후렴에서 더블링/하모니/애드리브 중 하나를 확장하세요.",
        ),
        _summary_from_counts(
            "hit_factor",
            "Hit Factor Pattern",
            top_hit_factors,
            "히트 포인트는 {label} 경향이 많이 보입니다.",
            "새 곡에서는 따라 부르기 쉬운 구간과 제목 기억성을 같은 위치에 묶어 설계하세요.",
        ),
        _summary_from_counts(
            "creative_principles",
            "Transferable Principles",
            top_transferable_principles,
            "내 곡에 적용할 원리로는 {label} 항목이 많이 축적되어 있습니다.",
            "원곡 표현을 가져오지 말고 의사결정 원리만 새 컨셉, 새 가사, 새 멜로디로 바꾸세요.",
        ),
    ]


def _composer_question_cards(
    songs: list[dict[str, Any]],
    analyses: list[dict[str, Any]],
    bpms: list[float],
    first_chorus_times: list[float],
) -> list[dict[str, Any]]:
    top_progression = _first_label(_counts(_meaningful_progression(analysis.get("harmony", {}).get("chorus_progression")) for analysis in analyses))
    top_hook = _first_label(_counts(analysis.get("hook", {}).get("primary_hook_type") for analysis in analyses))
    top_arrangement = _first_label(_counts(_collect_arrangement_features(analyses)))
    top_peak_position = _first_label(_counts(analysis.get("melody", {}).get("chorus_peak_position") for analysis in analyses))
    top_title_usage = _first_label(_counts(analysis.get("lyrics", {}).get("title_usage") for analysis in analyses))
    title_ratio = _title_in_chorus_ratio(analyses)
    return [
        {
            "question": "이 장르의 히트곡들은 평균 BPM이 어느 정도인가?",
            "answer": f"현재 저장된 Reference Song 기준 평균 BPM은 약 {round(mean(bpms), 1)}입니다." if bpms else "아직 BPM 통계를 낼 만큼 분석곡이 충분하지 않습니다.",
            "creative_use": "새 곡을 설계할 때 목표 BPM 범위를 먼저 정하고, 리듬보다 보컬 호흡과 레이어 변화를 함께 설계하세요.",
        },
        {
            "question": "후렴은 보통 몇 초쯤 등장하는가?",
            "answer": f"현재 데이터에서는 첫 후렴이 평균 약 {round(mean(first_chorus_times), 1)}초에 등장합니다." if first_chorus_times else "첫 후렴 시점 데이터가 아직 부족합니다.",
            "creative_use": "스트리밍 환경에서는 첫 후렴 진입 시점을 의도적으로 설계해 초반 이탈을 줄이는 것이 좋습니다.",
        },
        {
            "question": "가장 많이 쓰이는 코드 진행은 무엇인가?",
            "answer": f"가장 많이 관찰된 후렴 코드 진행은 {top_progression}입니다." if top_progression else "코드 진행 데이터가 아직 부족합니다.",
            "creative_use": "진행을 그대로 복제하지 말고, 긴장과 해결의 위치만 새 멜로디와 가사에 맞게 바꾸세요.",
        },
        {
            "question": "후크는 멜로디형, 가사형, 리듬형 중 무엇이 많은가?",
            "answer": f"현재 가장 많이 관찰된 후크 유형은 {top_hook}입니다." if top_hook else "후크 유형 데이터가 아직 부족합니다.",
            "creative_use": "후렴 첫 두 마디에서 제목, 짧은 리듬, 반복 모티브 중 무엇을 중심 장치로 둘지 결정하세요.",
        },
        {
            "question": "제목은 가사에서 어디에 배치되는가?",
            "answer": f"현재 제목 사용 방식은 {top_title_usage}가 가장 많이 보이며, 후렴 등장 비율은 {round(title_ratio * 100, 1)}%입니다." if top_title_usage else "제목 사용 위치 데이터가 아직 부족합니다.",
            "creative_use": "제목을 후렴 첫 줄이나 반복 문장에 연결하면 기억성을 높일 수 있습니다.",
        },
        {
            "question": "후렴 최고음은 보통 어느 위치에 나오는가?",
            "answer": f"현재 가장 많이 관찰된 최고음 위치는 {top_peak_position}입니다." if top_peak_position else "멜로디 최고음 위치 데이터가 아직 부족합니다.",
            "creative_use": "처음부터 최고음을 쓰기보다 후렴 후반부에 보상 지점으로 배치하는 전략을 검토하세요.",
        },
        {
            "question": "발라드 히트곡에서 자주 쓰이는 편곡 방식은 무엇인가?",
            "answer": f"현재 가장 많이 관찰된 편곡 특징은 {top_arrangement}입니다." if top_arrangement else "편곡 특징 데이터가 아직 부족합니다.",
            "creative_use": "초반 절제, 후렴 확장, 마지막 후렴 리프트 같은 구조 원리만 참고하고 특정 리프는 복제하지 마세요.",
        },
    ]


def _average_bpm_by(songs: list[dict[str, Any]], group_key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for song in songs:
        if song.get("bpm") is None:
            continue
        grouped[str(song.get(group_key) or "Unknown")].append(float(song["bpm"]))
    return [
        {"label": label, "average_bpm": round(mean(values), 2), "count": len(values)}
        for label, values in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)
    ]


def _collect_moods(analyses: list[dict[str, Any]]) -> list[Any]:
    values = []
    for analysis in analyses:
        values.extend(_as_list(analysis.get("concept", {}).get("mood")))
    return values


def _collect_arrangement_features(analyses: list[dict[str, Any]]) -> list[Any]:
    values = []
    fields = [
        "arrangement_build",
        "chorus_arrangement",
        "final_chorus_lift",
        "space_design",
        "intro_instruments",
        "verse_instruments",
        "pre_chorus_instruments",
    ]
    for analysis in analyses:
        arrangement = analysis.get("arrangement", {})
        for field in fields:
            values.extend(_as_list(arrangement.get(field)))
    return values


def _collect_vocal_treatments(analyses: list[dict[str, Any]]) -> list[Any]:
    values = []
    fields = ["vocal_tone", "verse_delivery", "chorus_delivery", "vocal_effects", "adlib_usage", "harmony", "backing_vocals"]
    for analysis in analyses:
        vocal = analysis.get("vocal", {})
        for field in fields:
            values.extend(_as_list(vocal.get(field)))
    return values


def _collect_hit_factors(analyses: list[dict[str, Any]]) -> list[Any]:
    values = []
    for analysis in analyses:
        hit_factor = analysis.get("hit_factor", {})
        values.extend(_as_list(hit_factor.get("main_hit_factor")))
        values.extend(_as_list(hit_factor.get("replay_factor")))
        values.extend(_as_list(hit_factor.get("title_memorability")))
    return values


def _collect_transferable_principles(analyses: list[dict[str, Any]]) -> list[Any]:
    values = []
    for analysis in analyses:
        values.extend(_as_list(analysis.get("takeaway", {}).get("transferable_principles")))
    return values


def _summary_from_counts(id_value: str, title: str, items: list[dict[str, Any]], template: str, takeaway: str) -> dict[str, Any]:
    if not items:
        return {
            "id": id_value,
            "title": title,
            "summary": "아직 충분한 데이터가 없습니다.",
            "producer_takeaway": "Reference Song Analysis 데이터를 더 쌓으면 이 항목의 신뢰도가 올라갑니다.",
            "confidence": "low",
        }
    label = items[0]["label"]
    count = items[0]["count"]
    return {
        "id": id_value,
        "title": title,
        "summary": template.format(label=label, count=count),
        "producer_takeaway": takeaway,
        "confidence": "medium" if count >= 3 else "low",
    }


def _chart_insight(title: str, items: list[dict[str, Any]]) -> str:
    if not items:
        return f"{title} 데이터가 아직 부족합니다."
    top = items[0]
    return f"현재 가장 큰 비중은 {top['label']}이며 {top['count']}회 관찰되었습니다."


def _counts(values: Iterable[Any]) -> list[dict[str, Any]]:
    counts = Counter(str(value) for value in values if _has_value(value))
    return [{"label": label, "count": count} for label, count in counts.most_common(10)]


def _first_label(items: list[dict[str, Any]]) -> str | None:
    return items[0]["label"] if items else None


def _decade(year: Any) -> str:
    if not year:
        return "Unknown"
    try:
        numeric_year = int(year)
    except (TypeError, ValueError):
        return "Unknown"
    return f"{numeric_year // 10 * 10}s"


def _bpm_bucket(bpm: Any) -> str:
    if bpm is None:
        return "Unknown"
    value = float(bpm)
    if value < 70:
        return "Under 70"
    if value < 85:
        return "70-84"
    if value < 100:
        return "85-99"
    if value < 120:
        return "100-119"
    if value < 140:
        return "120-139"
    return "140+"


def _final_chorus_expansion(analysis: dict[str, Any]) -> str | None:
    structure = analysis.get("structure", {})
    arrangement = analysis.get("arrangement", {})
    vocal = analysis.get("vocal", {})
    return (
        structure.get("final_chorus_expansion")
        or arrangement.get("final_chorus_lift")
        or arrangement.get("final_chorus")
        or vocal.get("adlib_usage")
        or vocal.get("adlib")
    )


def _title_in_chorus_ratio(analyses: list[dict[str, Any]]) -> float:
    usages = [analysis.get("lyrics", {}).get("title_usage") for analysis in analyses]
    if not usages:
        return 0
    return sum(1 for value in usages if _mentions_chorus(value)) / len(usages)


def _mentions_chorus(value: Any) -> bool:
    text = str(value or "").lower()
    return "chorus" in text or "후렴" in text


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value:
        return [value]
    return []


def _has_value(value: Any) -> bool:
    return value is not None and value != "" and value != []


def _meaningful_progression(value: Any) -> Any:
    if not _has_value(value):
        return None
    text = str(value).strip()
    lowered = text.lower()
    placeholders = [
        "user chords unavailable",
        "chord progression unavailable",
        "코드 진행 미입력",
        "미입력",
        "unavailable",
        "requires",
    ]
    if any(token in lowered for token in placeholders):
        return None
    return text
