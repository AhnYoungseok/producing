from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class SongCreate(BaseModel):
    title: str
    artist: Optional[str] = None
    genre: Optional[str] = None
    release_year: Optional[int] = None
    country: Optional[str] = None
    youtube_url: Optional[str] = None
    youtube_metadata: dict[str, Any] = Field(default_factory=dict)
    research_profile: dict[str, Any] = Field(default_factory=dict)
    file_name: Optional[str] = None
    duration: Optional[float] = None
    bpm: Optional[float] = None
    key: Optional[str] = None


class SongResponse(BaseModel):
    id: str
    title: str
    artist: Optional[str] = None
    genre: Optional[str] = None
    release_year: Optional[int] = None
    country: Optional[str] = None
    youtube_url: Optional[str] = None
    youtube_metadata: dict[str, Any] = Field(default_factory=dict)
    research_profile: dict[str, Any] = Field(default_factory=dict)
    file_name: Optional[str] = None
    duration: Optional[float] = None
    bpm: Optional[float] = None
    key: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    analysis_complete: bool = False


class SongListResponse(BaseModel):
    songs: list[SongResponse]
