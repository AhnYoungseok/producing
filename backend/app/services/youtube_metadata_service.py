from __future__ import annotations

import json
import re
from html import unescape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from fastapi import HTTPException


YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}


def validate_youtube_reference_url(youtube_url: str | None) -> str:
    if youtube_url is None or not youtube_url.strip():
        raise HTTPException(
            status_code=400,
            detail="YouTube 참고 링크는 필수입니다. 단, YouTube 오디오는 다운로드하거나 추출하지 않고 업로드한 오디오 파일만 분석합니다.",
        )
    value = youtube_url.strip()
    parsed = urlparse(value)
    host = parsed.netloc.lower()
    is_youtube_host = host in YOUTUBE_HOSTS or host.endswith(".youtube.com") or host.endswith(".youtu.be")
    if parsed.scheme not in {"http", "https"} or not is_youtube_host:
        raise HTTPException(status_code=400, detail="유효한 YouTube 참고 링크를 입력해 주세요.")
    return value


def collect_youtube_reference_metadata(youtube_url: str) -> dict[str, Any]:
    """Collect allowed reference metadata without accessing or extracting audio."""
    video_id = extract_video_id(youtube_url)
    metadata: dict[str, Any] = {
        "source": "youtube_reference_metadata",
        "url": youtube_url,
        "video_id": video_id,
        "title": None,
        "channel_name": None,
        "description": None,
        "thumbnail_url": None,
        "duration": None,
        "published_date": None,
        "view_count": None,
        "metadata_status": "partial",
        "policy": "Metadata only. YouTube audio is not downloaded, extracted, isolated, converted, streamed, or analyzed.",
    }

    metadata.update(_fetch_oembed_metadata(youtube_url))
    page_metadata = _fetch_page_meta(youtube_url)
    for key, value in page_metadata.items():
        if value and not metadata.get(key):
            metadata[key] = value

    if metadata.get("title") or metadata.get("channel_name") or metadata.get("thumbnail_url"):
        metadata["metadata_status"] = "available"
    return metadata


def extract_video_id(youtube_url: str) -> str | None:
    parsed = urlparse(youtube_url)
    host = parsed.netloc.lower()
    if host.endswith("youtu.be"):
        return parsed.path.strip("/") or None
    query = parse_qs(parsed.query)
    if "v" in query and query["v"]:
        return query["v"][0]
    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) >= 2 and path_parts[0] in {"shorts", "embed", "live"}:
        return path_parts[1]
    return None


def _fetch_oembed_metadata(youtube_url: str) -> dict[str, Any]:
    endpoint = "https://www.youtube.com/oembed?" + urlencode({"url": youtube_url, "format": "json"})
    try:
        body = _http_get(endpoint, timeout=4)
        payload = json.loads(body)
    except (HTTPError, URLError, TimeoutError, ValueError, OSError):
        return {}
    return {
        "title": payload.get("title"),
        "channel_name": payload.get("author_name"),
        "thumbnail_url": payload.get("thumbnail_url"),
    }


def _fetch_page_meta(youtube_url: str) -> dict[str, Any]:
    try:
        html = _http_get(youtube_url, timeout=5)
    except (HTTPError, URLError, TimeoutError, OSError):
        return {}
    return {
        "title": _meta_content(html, ["og:title", "twitter:title", "title"]),
        "channel_name": _meta_content(html, ["og:video:tag", "twitter:creator"]) or _json_value(html, "ownerChannelName"),
        "description": _meta_content(html, ["og:description", "description", "twitter:description"]),
        "thumbnail_url": _meta_content(html, ["og:image", "twitter:image"]),
        "duration": _meta_content(html, ["duration"]) or _json_value(html, "lengthSeconds"),
        "published_date": _meta_content(html, ["datePublished", "uploadDate"]) or _json_value(html, "publishDate"),
        "view_count": _meta_content(html, ["interactionCount"]) or _json_value(html, "viewCount"),
    }


def _http_get(url: str, timeout: int) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "HitSongLab/0.1 metadata-only reference client",
            "Accept": "text/html,application/json",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read(1_000_000)
    return raw.decode("utf-8", errors="replace")


def _meta_content(html: str, names: list[str]) -> str | None:
    for name in names:
        patterns = [
            rf'<meta[^>]+(?:property|name|itemprop)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name|itemprop)=["\']{re.escape(name)}["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, flags=re.IGNORECASE)
            if match:
                return unescape(match.group(1)).strip()
    return None


def _json_value(html: str, key: str) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*"([^"]+)"', html)
    if match:
        return unescape(match.group(1)).strip()
    return None
