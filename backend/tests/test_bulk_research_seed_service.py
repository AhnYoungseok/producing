from app.db.database import SQLiteStore
from app.services.genre_bestseller_service import import_bulk_research_seeds


def test_bulk_research_seeds_are_disabled(tmp_path):
    store = SQLiteStore(tmp_path / "hit_song_lab_test.db")
    store.init_schema()

    first = import_bulk_research_seeds(store, target_count=25, batch_size=25)
    second = import_bulk_research_seeds(store, target_count=25, batch_size=25)

    assert first["created_count"] == 0
    assert first["bulk_seed_total"] == 0
    assert first["library_statistics"]["summary"]["song_count"] == 0
    assert "disabled" in first["disabled_reason"].lower()
    assert second["created_count"] == 0
    assert second["bulk_seed_total"] == 0
    assert second["library_statistics"]["summary"]["song_count"] == 0


def test_duplicate_song_identity_reuses_existing_song(tmp_path):
    store = SQLiteStore(tmp_path / "hit_song_lab_test.db")
    store.init_schema()

    first = store.create_song({"title": "Never Gonna Give You Up", "artist": "Rick Astley"})
    second = store.create_song({"title": "Never Gonna Give You Up (4K Remaster)", "artist": "Rick Astley"})

    assert second["id"] == first["id"]
    assert len(store.list_songs()) == 1
