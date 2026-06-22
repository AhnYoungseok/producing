from app.services.hit_song_researcher import build_analysis_from_research_profile, build_hit_song_research_profile


def test_hit_song_research_profile_uses_metadata_and_confidence(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.hit_song_researcher.collect_youtube_reference_metadata",
        lambda url: {
            "url": url,
            "title": "Artist Name - Big Hit (Official Music Video)",
            "channel_name": "Artist Name",
            "description": "A pop ballad about love and missing someone.",
            "duration": "PT3M30S",
            "thumbnail_url": "https://img.example/thumb.jpg",
            "published_date": "2020-01-01",
            "view_count": "123456",
            "metadata_status": "available",
        },
    )
    monkeypatch.setattr(
        "app.services.hit_song_researcher.collect_public_music_data",
        lambda title, artist: {
            "musicbrainz": {"status": "available", "title": title, "artist": artist, "release_year": 2020, "tags": ["pop", "ballad"]},
            "lastfm": {"status": "not_configured", "source": "Last.fm"},
            "spotify": {"status": "not_configured", "source": "Spotify"},
        },
    )

    profile = build_hit_song_research_profile(
        "https://www.youtube.com/watch?v=abc",
        lyrics_text="I miss you and I still love you",
        chord_progression="Verse: I - V - vi - IV",
        analysis_notes="72 BPM, A major, chorus feels like a lyric hook",
    )
    analysis = build_analysis_from_research_profile(profile)

    assert profile["identification"]["title"]["value"] == "Big Hit"
    assert profile["identification"]["artist"]["confidence"] == "high"
    assert profile["musical_features"]["bpm"]["value"] == 72
    assert profile["musical_features"]["bpm"]["confidence"] == "low"
    assert profile["safe_design_policy"]["youtube_role"] == "reference metadata only"
    assert analysis["audio_features"]["analysis_source"] == "youtube_link_research_profile_no_youtube_audio"
    assert analysis["lyrics"]["core_message"]
    assert analysis["harmony"]["verse_progression"] == "I - V - vi - IV"
    assert analysis["harmony"]["has_user_chords"] is True
    assert "Do not reuse the original melody line." in analysis["takeaway"]["avoid_copying"]
