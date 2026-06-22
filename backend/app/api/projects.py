from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.db.database import SQLiteStore
from app.models.blueprint import BlueprintResponse
from app.models.project import ProjectCreate, ProjectResponse
from app.services.pattern_miner import extract_patterns
from app.services.song_blueprint_generator import generate_song_blueprint

router = APIRouter()
store = SQLiteStore(settings.database_path)


@router.post("/projects", response_model=ProjectResponse)
def create_project(payload: ProjectCreate) -> ProjectResponse:
    project = store.create_project(payload.model_dump())
    return ProjectResponse(**project)


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects() -> list[ProjectResponse]:
    return [ProjectResponse(**project) for project in store.list_projects()]


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str) -> ProjectResponse:
    project = store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    return ProjectResponse(**project)


@router.post("/projects/{project_id}/blueprint", response_model=BlueprintResponse)
def create_blueprint(project_id: str) -> BlueprintResponse:
    project = store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    songs = [song for song in (store.get_song(song_id) for song_id in project["reference_song_ids"]) if song is not None]
    analyses = store.get_analyses_for_songs([song["id"] for song in songs])
    mined_patterns = extract_patterns(songs, analyses, ["concept", "lyrics", "harmony", "hook", "structure", "arrangement"]) if analyses else []
    blueprint = generate_song_blueprint(project, songs, analyses, mined_patterns)
    store.update_project_plans(project_id, blueprint)
    saved = store.save_blueprint(project_id, blueprint)
    return BlueprintResponse(**saved)


@router.get("/projects/{project_id}/blueprint", response_model=BlueprintResponse)
def get_blueprint(project_id: str) -> BlueprintResponse:
    blueprint = store.get_blueprint(project_id)
    if blueprint is None:
        raise HTTPException(status_code=404, detail="신곡 제작 설계도를 찾을 수 없습니다.")
    return BlueprintResponse(**blueprint)
