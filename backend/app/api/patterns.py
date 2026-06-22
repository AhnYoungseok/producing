from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.db.database import SQLiteStore
from app.models.pattern import PatternExtractRequest, PatternResponse
from app.services.pattern_miner import extract_patterns

router = APIRouter()
store = SQLiteStore(settings.database_path)


@router.post("/patterns/extract", response_model=list[PatternResponse])
def extract_song_patterns(payload: PatternExtractRequest) -> list[PatternResponse]:
    songs = [song for song in (store.get_song(song_id) for song_id in payload.song_ids) if song is not None]
    if not songs:
        raise HTTPException(status_code=400, detail="패턴을 추출할 곡을 선택해 주세요.")
    analyses = store.get_analyses_for_songs([song["id"] for song in songs])
    if not analyses:
        raise HTTPException(status_code=400, detail="선택한 곡에 저장된 분석 데이터가 없습니다.")
    mined = extract_patterns(songs, analyses, payload.pattern_types)
    saved = [store.save_pattern(pattern) for pattern in mined]
    return [PatternResponse(**pattern) for pattern in saved]


@router.get("/patterns", response_model=list[PatternResponse])
def list_patterns() -> list[PatternResponse]:
    return [PatternResponse(**pattern) for pattern in store.list_patterns()]
