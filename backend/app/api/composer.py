from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.db.database import SQLiteStore
from app.services.blueprint_updater import (
    apply_user_turn,
    attach_assistant_turn,
    initialize_interactive_blueprint,
    project_plan_updates,
)
from app.services.conversation_coach import compose_assistant_turn
from app.services.recommendation_service import build_reference_recommendations

router = APIRouter()
store = SQLiteStore(settings.database_path)


class ComposerChatRequest(BaseModel):
    message: str | None = None
    selected_option_id: str | None = None


class ComposerChatResponse(BaseModel):
    project_id: str
    stage: int
    stage_title: str
    assistant_message: str
    options: list[dict[str, Any]]
    recommendations: dict[str, Any] | None = None
    blueprint: dict[str, Any]


@router.get("/composer/{project_id}")
def composer_project(project_id: str) -> dict[str, Any]:
    project = store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    blueprint = _get_or_initialize_blueprint(project)
    return {"project": project, "blueprint": blueprint}


@router.post("/composer/{project_id}/chat", response_model=ComposerChatResponse)
def composer_chat(project_id: str, payload: ComposerChatRequest) -> ComposerChatResponse:
    project = store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

    blueprint_row = _get_or_initialize_blueprint(project)
    blueprint = blueprint_row["blueprint_json"]
    blueprint = apply_user_turn(project, blueprint, payload.message, payload.selected_option_id)

    songs, analyses = _project_reference_context(project)
    recommendations = build_reference_recommendations(project, songs, analyses, payload.message)
    coach_turn = compose_assistant_turn(project, blueprint, recommendations)
    blueprint = attach_assistant_turn(
        blueprint,
        coach_turn["assistant_message"],
        coach_turn["options"],
        coach_turn.get("recommendations"),
    )

    store.update_project_plans(project_id, project_plan_updates(blueprint))
    saved = store.save_blueprint(project_id, blueprint)

    return ComposerChatResponse(
        project_id=project_id,
        stage=coach_turn["stage"],
        stage_title=coach_turn["stage_title"],
        assistant_message=coach_turn["assistant_message"],
        options=coach_turn["options"],
        recommendations=coach_turn.get("recommendations"),
        blueprint=saved,
    )


def _get_or_initialize_blueprint(project: dict[str, Any]) -> dict[str, Any]:
    existing_row = store.get_blueprint(project["id"])
    existing_json = existing_row["blueprint_json"] if existing_row else None
    initialized = initialize_interactive_blueprint(project, existing_json)
    if existing_row is None or initialized != existing_json:
        return store.save_blueprint(project["id"], initialized)
    return existing_row


def _project_reference_context(project: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    songs = [song for song in (store.get_song(song_id) for song_id in project["reference_song_ids"]) if song is not None]
    analyses = store.get_analyses_for_songs([song["id"] for song in songs])
    return songs, analyses
