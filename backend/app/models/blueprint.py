from datetime import datetime
from typing import Any

from pydantic import BaseModel


class BlueprintResponse(BaseModel):
    id: str
    project_id: str
    blueprint_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime
