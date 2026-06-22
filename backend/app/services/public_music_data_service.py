from __future__ import annotations

import base64
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import settings


USER_AGENT = "HitSongLab/0.1 (metadata-only research; no audio extraction)"


def collect_public_music_data(title: str | None, artist: str | None) -> dict[str, Any]:
    return {
        "musicbrainz": lookup_musicbrainz(title, artist),
        "lastfm": lookup_lastfm(title, artist),
        "spotify": lookup_spotify(title, artist),
    }


def lookup_musicbrainz(title: str | None, artist: str | None) -> dict[str, Any]:
    if not title:
        return {"status": "skipped", "reason": "missing_title"}
    query_parts = [f'recording:"{title}"']
    if artist:
        query_parts.append(f'artist:"{artist}"')
    url = "https://musicbrainz.org/ws/2/recording?" + urlencode({"query": " AND ".join(query_parts), "fmt": "json", "limit": "3"})
    try:
        payload = _get_json(url, timeout=6)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        return {"status": "unavailable", "reason": str(exc)}
    recordings = payload.get("recordings", [])
    if not recordings:
        return {"status": "not_found"}
    first = recordings[0]
    artist_credit = first.get("artist-credit", [])
    artist_name = artist_credit[0].get("name") if artist_credit else None
    release_date = first.get("first-release-date")
    tags = [tag.get("name") for tag in first.get("tags", []) if tag.get("name")]
    return {
        "status": "available",
        "title": first.get("title"),
        "artist": artist_name,
        "first_release_date": release_date,
        "release_year": _year_from_date(release_date),
        "tags": tags[:10],
        "score": first.get("score"),
        "source": "MusicBrainz",
    }


def lookup_lastfm(title: str | None, artist: str | None) -> dict[str, Any]:
    if not settings.lastfm_api_key:
        return {"status": "not_configured", "source": "Last.fm"}
    if not title or not artist:
        return {"status": "skipped", "reason": "missing_title_or_artist", "source": "Last.fm"}
    url = "https://ws.audioscrobbler.com/2.0/?" + urlencode(
        {
            "method": "track.getInfo",
            "api_key": settings.lastfm_api_key,
            "artist": artist,
            "track": title,
            "format": "json",
        }
    )
    try:
        payload = _get_json(url, timeout=6)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        return {"status": "unavailable", "reason": str(exc), "source": "Last.fm"}
    track = payload.get("track")
    if not track:
        return {"status": "not_found", "source": "Last.fm"}
    tags = [tag.get("name") for tag in track.get("toptags", {}).get("tag", []) if tag.get("name")]
    return {
        "status": "available",
        "listeners": _safe_int(track.get("listeners")),
        "playcount": _safe_int(track.get("playcount")),
        "tags": tags[:10],
        "source": "Last.fm",
    }


def lookup_spotify(title: str | None, artist: str | None) -> dict[str, Any]:
    if not settings.spotify_client_id or not settings.spotify_client_secret:
        return {"status": "not_configured", "source": "Spotify"}
    if not title:
        return {"status": "skipped", "reason": "missing_title", "source": "Spotify"}
    token = _spotify_token()
    if token is None:
        return {"status": "unavailable", "reason": "token_request_failed", "source": "Spotify"}
    query = f'track:"{title}"'
    if artist:
        query += f' artist:"{artist}"'
    search_url = "https://api.spotify.com/v1/search?" + urlencode({"q": query, "type": "track", "limit": "1"})
    try:
        search_payload = _get_json(search_url, timeout=6, bearer_token=token)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        return {"status": "unavailable", "reason": str(exc), "source": "Spotify"}
    items = search_payload.get("tracks", {}).get("items", [])
    if not items:
        return {"status": "not_found", "source": "Spotify"}
    track = items[0]
    result: dict[str, Any] = {
        "status": "available",
        "source": "Spotify",
        "spotify_track_id": track.get("id"),
        "title": track.get("name"),
        "artist": ", ".join(artist_item.get("name", "") for artist_item in track.get("artists", [])),
        "popularity": track.get("popularity"),
        "release_date": track.get("album", {}).get("release_date"),
        "release_year": _year_from_date(track.get("album", {}).get("release_date")),
    }
    audio_features = _lookup_spotify_audio_features(track.get("id"), token)
    if audio_features:
        result["audio_features"] = audio_features
    return result


def _lookup_spotify_audio_features(track_id: str | None, token: str) -> dict[str, Any] | None:
    if not track_id:
        return None
    url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    try:
        payload = _get_json(url, timeout=6, bearer_token=token)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return None
    return {
        "tempo": payload.get("tempo"),
        "key": payload.get("key"),
        "mode": payload.get("mode"),
        "energy": payload.get("energy"),
        "danceability": payload.get("danceability"),
        "valence": payload.get("valence"),
        "duration_ms": payload.get("duration_ms"),
    }


def _spotify_token() -> str | None:
    credentials = f"{settings.spotify_client_id}:{settings.spotify_client_secret}".encode("utf-8")
    request = Request(
        "https://accounts.spotify.com/api/token",
        data=urlencode({"grant_type": "client_credentials"}).encode("utf-8"),
        headers={
            "Authorization": f"Basic {base64.b64encode(credentials).decode('ascii')}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=6) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return None
    return payload.get("access_token")


def _get_json(url: str, timeout: int, bearer_token: str | None = None) -> dict[str, Any]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _year_from_date(value: str | None) -> int | None:
    if not value or len(value) < 4:
        return None
    try:
        return int(value[:4])
    except ValueError:
        return None


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
