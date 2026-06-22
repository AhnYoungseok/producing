from fastapi import APIRouter, Query

from app.services.youtube_metadata_service import collect_youtube_reference_metadata, validate_youtube_reference_url

router = APIRouter()


@router.get("/youtube/metadata")
def youtube_metadata(url: str = Query(..., min_length=1)) -> dict:
    normalized_url = validate_youtube_reference_url(url)
    return collect_youtube_reference_metadata(normalized_url)
