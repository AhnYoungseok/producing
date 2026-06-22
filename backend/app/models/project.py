from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    title: str
    target_genre: Optional[str] = None
    target_mood: Optional[str] = None
    target_listener: Optional[str] = None
    reference_song_ids: list[str] = []
    theme: Optional[str] = None
    vocal_style: Optional[str] = None
    bpm_range: Optional[str] = None
    lyric_language: Optional[str] = "한국어"
    instruments: Optional[str] = None
    arrangement_style: Optional[str] = None


class ProjectResponse(ProjectCreate):
    id: str
    concept_json: dict
    lyrics_plan_json: dict
    harmony_plan_json: dict
    melody_plan_json: dict
    hook_plan_json: dict
    arrangement_plan_json: dict
    created_at: datetime
    updated_at: datetime
