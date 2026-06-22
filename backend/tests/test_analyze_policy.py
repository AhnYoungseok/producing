import pytest
from fastapi import HTTPException

from app.api.analyze import validate_youtube_reference_url
from app.services.youtube_metadata_service import collect_youtube_reference_metadata, extract_video_id


def test_youtube_reference_url_is_required() -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_youtube_reference_url("")

    assert exc_info.value.status_code == 400


def test_youtube_reference_url_must_be_youtube_host() -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_youtube_reference_url("https://example.com/watch?v=abc")

    assert exc_info.value.status_code == 400


def test_youtube_reference_url_accepts_youtube() -> None:
    assert validate_youtube_reference_url("https://www.youtube.com/watch?v=abc") == "https://www.youtube.com/watch?v=abc"
    assert validate_youtube_reference_url("https://youtu.be/abc") == "https://youtu.be/abc"


def test_extract_video_id_from_common_youtube_urls() -> None:
    assert extract_video_id("https://www.youtube.com/watch?v=abc123") == "abc123"
    assert extract_video_id("https://youtu.be/abc123") == "abc123"
    assert extract_video_id("https://www.youtube.com/shorts/abc123") == "abc123"


def test_collect_youtube_metadata_is_metadata_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.youtube_metadata_service._fetch_oembed_metadata",
        lambda url: {"title": "Reference Title", "channel_name": "Reference Channel", "thumbnail_url": "https://img.example/thumb.jpg"},
    )
    monkeypatch.setattr(
        "app.services.youtube_metadata_service._fetch_page_meta",
        lambda url: {"description": "Reference description", "duration": "PT3M20S", "published_date": "2024-01-01", "view_count": "123"},
    )

    metadata = collect_youtube_reference_metadata("https://www.youtube.com/watch?v=abc123")

    assert metadata["title"] == "Reference Title"
    assert metadata["duration"] == "PT3M20S"
    assert metadata["metadata_status"] == "available"
    assert "not downloaded" in metadata["policy"]
