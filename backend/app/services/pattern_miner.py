from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any, Iterable


def extract_patterns(songs: list[dict[str, Any]], analyses: list[dict[str, Any]], pattern_types: list[str]) -> list[dict[str, Any]]:
    requested = set(pattern_types or ["concept", "lyrics", "harmony", "hook", "arrangement"])
    genre = most_common(song.get("genre") for song in songs) or "Mixed"
    source_song_ids = [song["id"] for song in songs]
    patterns: list[dict[str, Any]] = []

    pattern_builders = {
        "concept": _concept_pattern,
        "lyrics": _lyrics_pattern,
        "harmony": _harmony_pattern,
        "melody": _melody_pattern,
        "hook": _hook_pattern,
        "structure": _structure_pattern,
        "arrangement": _arrangement_pattern,
        "vocal": _vocal_pattern,
        "mixing": _mixing_pattern,
        "hit_factor": _hit_factor_pattern,
    }

    for pattern_type, builder in pattern_builders.items():
        if pattern_type in requested:
            patterns.append(builder(genre, source_song_ids, songs, analyses))

    bpms = [song.get("bpm") for song in songs if song.get("bpm") is not None]
    if bpms:
        for pattern in patterns:
            pattern["pattern_json"]["average_bpm"] = round(mean(float(bpm) for bpm in bpms), 2)

    return patterns


def _concept_pattern(genre: str, source_song_ids: list[str], songs: list[dict[str, Any]], analyses: list[dict[str, Any]]) -> dict[str, Any]:
    moods = flatten(analysis["concept"].get("mood", []) for analysis in analyses)
    common_moods = top_counts(moods)
    return make_pattern(
        "concept",
        genre,
        f"{genre} 레퍼런스에서는 {join_labels(common_moods)} 정서가 반복적으로 관찰됩니다.",
        source_song_ids,
        {
            "common_moods": common_moods,
            "creative_use": "새 곡의 컨셉은 공통 정서 중 하나를 선택하되, 새로운 화자와 상황으로 바꿔 설계합니다.",
        },
    )


def _lyrics_pattern(genre: str, source_song_ids: list[str], songs: list[dict[str, Any]], analyses: list[dict[str, Any]]) -> dict[str, Any]:
    phrase_types = top_counts(analysis["lyrics"].get("chorus_key_phrase_type") for analysis in analyses)
    title_usage = top_counts(analysis["lyrics"].get("title_usage") for analysis in analyses)
    return make_pattern(
        "lyrics",
        genre,
        f"후렴 핵심 문장은 {join_labels(phrase_types)} 유형이 많이 관찰됩니다.",
        source_song_ids,
        {
            "chorus_phrase_types": phrase_types,
            "title_usage": title_usage,
            "creative_use": "후렴 첫 줄에 제목과 연결되는 짧은 새 문장을 배치하면 기억성을 높일 수 있습니다.",
        },
    )


def _harmony_pattern(genre: str, source_song_ids: list[str], songs: list[dict[str, Any]], analyses: list[dict[str, Any]]) -> dict[str, Any]:
    chorus_progressions = top_counts(analysis["harmony"].get("chorus_progression") for analysis in analyses)
    return make_pattern(
        "harmony",
        genre,
        f"후렴 코드 진행은 {join_labels(chorus_progressions)} 계열이 반복됩니다.",
        source_song_ids,
        {
            "chorus_progressions": chorus_progressions,
            "creative_use": "진행 자체를 복제하지 말고 후렴 시작의 긴장과 해결 위치를 새 멜로디에 맞게 재설계합니다.",
        },
    )


def _melody_pattern(genre: str, source_song_ids: list[str], songs: list[dict[str, Any]], analyses: list[dict[str, Any]]) -> dict[str, Any]:
    peak_positions = top_counts(analysis["melody"].get("chorus_peak_position") for analysis in analyses)
    motif_types = top_counts(analysis["melody"].get("motif_type") for analysis in analyses)
    return make_pattern(
        "melody",
        genre,
        f"후렴 최고음 위치는 {join_labels(peak_positions)} 패턴이 자주 보입니다.",
        source_song_ids,
        {
            "chorus_peak_positions": peak_positions,
            "motif_types": motif_types,
            "creative_use": "최고음을 처음부터 쓰기보다 후렴 후반부의 감정 보상 지점으로 설계합니다.",
        },
    )


def _hook_pattern(genre: str, source_song_ids: list[str], songs: list[dict[str, Any]], analyses: list[dict[str, Any]]) -> dict[str, Any]:
    hook_types = top_counts(analysis["hook"].get("primary_hook_type") for analysis in analyses)
    return make_pattern(
        "hook",
        genre,
        f"강한 후크는 {join_labels(hook_types)} 방식으로 반복되는 경우가 많습니다.",
        source_song_ids,
        {
            "hook_types": hook_types,
            "creative_use": "기존 후크를 차용하지 말고 후렴 첫 두 마디에 새 가사와 새 리듬을 결합합니다.",
        },
    )


def _structure_pattern(genre: str, source_song_ids: list[str], songs: list[dict[str, Any]], analyses: list[dict[str, Any]]) -> dict[str, Any]:
    structures = top_counts(" - ".join(analysis["structure"].get("structure", [])) for analysis in analyses)
    first_chorus_times = [
        float(analysis["structure"].get("first_chorus_time"))
        for analysis in analyses
        if analysis["structure"].get("first_chorus_time") is not None
    ]
    return make_pattern(
        "structure",
        genre,
        f"대표 구조는 {join_labels(structures)} 흐름으로 요약됩니다.",
        source_song_ids,
        {
            "structures": structures,
            "average_first_chorus_time": round(mean(first_chorus_times), 2) if first_chorus_times else None,
            "creative_use": "벌스 절제, 후렴 집중, 마지막 후렴 확장 같은 에너지 곡선 원리를 참고합니다.",
        },
    )


def _arrangement_pattern(genre: str, source_song_ids: list[str], songs: list[dict[str, Any]], analyses: list[dict[str, Any]]) -> dict[str, Any]:
    builds = top_counts(analysis["arrangement"].get("arrangement_build") for analysis in analyses)
    final_lifts = top_counts(analysis["arrangement"].get("final_chorus_lift") for analysis in analyses)
    return make_pattern(
        "arrangement",
        genre,
        f"편곡은 {join_labels(builds)} 방식으로 감정을 확장하는 경향이 있습니다.",
        source_song_ids,
        {
            "arrangement_builds": builds,
            "final_chorus_lifts": final_lifts,
            "creative_use": "악기 추가 타이밍은 참고하되 특정 리프와 사운드 시그니처는 새롭게 디자인합니다.",
        },
    )


def _vocal_pattern(genre: str, source_song_ids: list[str], songs: list[dict[str, Any]], analyses: list[dict[str, Any]]) -> dict[str, Any]:
    tones = top_counts(analysis["vocal"].get("vocal_tone") for analysis in analyses)
    deliveries = top_counts(analysis["vocal"].get("chorus_delivery") for analysis in analyses)
    return make_pattern(
        "vocal",
        genre,
        f"보컬은 {join_labels(tones)} 톤과 {join_labels(deliveries)} 후렴 전달 방식이 자주 관찰됩니다.",
        source_song_ids,
        {
            "vocal_tones": tones,
            "chorus_deliveries": deliveries,
            "creative_use": "벌스의 거리감과 후렴의 발성 확장을 대비시켜 새 곡의 감정선을 만듭니다.",
        },
    )


def _mixing_pattern(genre: str, source_song_ids: list[str], songs: list[dict[str, Any]], analyses: list[dict[str, Any]]) -> dict[str, Any]:
    vocal_positions = top_counts(analysis["mixing"].get("vocal_position") for analysis in analyses)
    stereo_widths = top_counts(analysis["mixing"].get("stereo_width") for analysis in analyses)
    return make_pattern(
        "mixing",
        genre,
        f"믹스에서는 보컬 위치 {join_labels(vocal_positions)} 성향이 반복됩니다.",
        source_song_ids,
        {
            "vocal_positions": vocal_positions,
            "stereo_widths": stereo_widths,
            "creative_use": "보컬 전면감, 저역 밀도, 공간감의 비율을 새 곡 장르에 맞게 재설계합니다.",
        },
    )


def _hit_factor_pattern(genre: str, source_song_ids: list[str], songs: list[dict[str, Any]], analyses: list[dict[str, Any]]) -> dict[str, Any]:
    factors = top_counts(analysis["hit_factor"].get("main_hit_factor") for analysis in analyses)
    replay = top_counts(analysis["hit_factor"].get("replay_factor") for analysis in analyses)
    return make_pattern(
        "hit_factor",
        genre,
        f"히트 포인트는 {join_labels(factors)} 요소가 중심으로 나타납니다.",
        source_song_ids,
        {
            "main_hit_factors": factors,
            "replay_factors": replay,
            "creative_use": "대중성 요소를 표면적으로 모방하지 말고 기억성, 감정 이입, 반복 청취 장치로 일반화합니다.",
        },
    )


def make_pattern(pattern_type: str, genre: str, description: str, source_song_ids: list[str], pattern_json: dict[str, Any]) -> dict[str, Any]:
    confidence = "high" if len(source_song_ids) >= 8 else "medium" if len(source_song_ids) >= 3 else "low"
    pattern_json["source_song_count"] = len(source_song_ids)
    pattern_json["confidence"] = confidence
    return {
        "pattern_type": pattern_type,
        "genre": genre,
        "description": description,
        "source_song_ids": source_song_ids,
        "pattern_json": pattern_json,
    }


def most_common(values: Iterable[Any]) -> str | None:
    counts = Counter(value for value in values if value)
    return counts.most_common(1)[0][0] if counts else None


def top_counts(values: Iterable[Any]) -> list[dict[str, Any]]:
    counts = Counter(str(value) for value in values if value is not None and value != "" and value != [])
    return [{"label": label, "count": count} for label, count in counts.most_common(5)]


def flatten(groups: Iterable[Iterable[Any]]) -> list[str]:
    output: list[str] = []
    for group in groups:
        output.extend([str(item) for item in group if item])
    return output


def join_labels(items: list[dict[str, Any]]) -> str:
    if not items:
        return "아직 충분한 데이터 없음"
    return ", ".join(item["label"] for item in items[:3])
