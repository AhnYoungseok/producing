from app.db.database import SQLiteStore
from app.services.genre_bestseller_service import import_genre_bestsellers, supported_bestseller_genres


def test_import_genre_bestsellers_creates_top_10_with_statistics(tmp_path) -> None:
    store = SQLiteStore(tmp_path / "hit_song_lab.db")
    store.init_schema()

    result = import_genre_bestsellers(store, "K-pop Ballad", limit=10)

    songs = store.list_songs(genre="K-pop Ballad")
    analyses = store.get_analyses_for_songs([song["id"] for song in songs])

    assert result["imported_count"] == 10
    assert result["created_count"] == 10
    assert len(songs) == 10
    assert len(analyses) == 10
    assert result["genre_statistics"]["summary"]["average_bpm"] > 0
    assert result["genre_statistics"]["top_chorus_progressions"]
    assert result["youtube_policy"].startswith("YouTube is used only")


def test_supported_bestseller_genres_exposes_catalog() -> None:
    genres = supported_bestseller_genres()

    assert any(item["genre"] == "K-pop Ballad" for item in genres)
    assert any(item["genre"] == "Global Pop" for item in genres)
    assert all(item["song_count"] == 10 for item in genres)
