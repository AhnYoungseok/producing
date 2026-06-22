from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class PatternExtractRequest(BaseModel):
    song_ids: list[str]
    pattern_types: list[str]


class PatternResponse(BaseModel):
    id: str
    pattern_type: str
    genre: Optional[str] = None
    description: str
    source_song_ids: list[str]
    pattern_json: dict[str, Any]
    created_at: datetime
