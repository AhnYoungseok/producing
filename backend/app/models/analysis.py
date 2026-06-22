from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AudioFeatures(BaseModel):
    bpm: float
    estimated_key: str
    duration_seconds: float
    loudness_estimate: float
    onset_density: float
    spectral_centroid_mean: float
    zero_crossing_rate_mean: float
    chroma_summary: dict[str, float]


class AnalysisSections(BaseModel):
    concept: dict[str, Any]
    lyrics: dict[str, Any]
    structure: dict[str, Any]
    harmony: dict[str, Any]
    melody: dict[str, Any]
    hook: dict[str, Any]
    rhythm: dict[str, Any]
    arrangement: dict[str, Any]
    vocal: dict[str, Any]
    mixing: dict[str, Any]
    hit_factor: dict[str, Any]
    takeaway: dict[str, Any]


class SongAnalysisResponse(AnalysisSections):
    id: str
    song_id: str
    audio_features: AudioFeatures
    full_report: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AnalyzeResponse(BaseModel):
    song: dict[str, Any]
    analysis: SongAnalysisResponse
