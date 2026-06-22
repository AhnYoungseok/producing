from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.db.database import SQLiteStore, make_id
from app.services.arrangement_analyzer import analyze_arrangement
from app.services.audio_processor import convert_to_wav, save_upload_file
from app.services.concept_analyzer import analyze_concept
from app.services.harmony_analyzer import analyze_harmony
from app.services.hook_analyzer import analyze_hook
from app.services.library_exporter import export_store_snapshot
from app.services.lyric_analyzer import analyze_lyrics
from app.services.melody_analyzer import analyze_melody
from app.services.music_analyzer import analyze_audio as analyze_music
from app.services.report_generator import build_hit_factor, build_takeaway, generate_full_report
from app.services.vocal_mixing_analyzer import analyze_mixing, analyze_vocal
from app.services.youtube_metadata_service import collect_youtube_reference_metadata, validate_youtube_reference_url

router = APIRouter()
store = SQLiteStore(settings.database_path)


@router.post("/analyze")
async def analyze_song(
    audio_file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    artist: Optional[str] = Form(default=None),
    genre: Optional[str] = Form(default=None),
    release_year: Optional[int] = Form(default=None),
    country: Optional[str] = Form(default=None),
    youtube_url: Optional[str] = Form(default=None),
    lyrics_text: Optional[str] = Form(default=None),
    chord_progression: Optional[str] = Form(default=None),
    analysis_notes: Optional[str] = Form(default=None),
) -> dict:
    normalized_youtube_url = validate_youtube_reference_url(youtube_url)
    youtube_metadata = collect_youtube_reference_metadata(normalized_youtube_url)
    song_id = make_id("song")
    try:
        original_path = await save_upload_file(audio_file, settings.storage_path, song_id)
        wav_path = convert_to_wav(original_path, settings.storage_path / song_id)
        music = analyze_music(wav_path)
        audio_features = music["audio_features"]
        structure = music["structure_estimate"]
        metadata = {
            "id": song_id,
            "title": title or youtube_metadata.get("title") or Path(audio_file.filename or "Untitled Song").stem,
            "artist": artist or youtube_metadata.get("channel_name"),
            "genre": genre,
            "release_year": release_year,
            "country": country,
            "youtube_url": normalized_youtube_url,
            "youtube_metadata": youtube_metadata,
            "file_name": Path(audio_file.filename or original_path.name).name,
            "duration": audio_features["duration_seconds"],
            "bpm": audio_features["bpm"],
            "key": audio_features["estimated_key"],
            "analysis_notes": analysis_notes,
        }
        song = store.create_song(metadata)
        concept = analyze_concept(metadata, audio_features, lyrics_text)
        lyrics = analyze_lyrics(lyrics_text, metadata["title"])
        harmony = analyze_harmony(chord_progression, audio_features)
        melody = analyze_melody(audio_features, lyrics)
        hook = analyze_hook(lyrics, metadata, audio_features)
        rhythm = build_rhythm(audio_features)
        arrangement = analyze_arrangement(metadata, audio_features, structure)
        vocal = analyze_vocal(metadata, lyrics)
        mixing = analyze_mixing(audio_features)
        sections = {
            "concept": concept,
            "lyrics": lyrics,
            "structure": structure,
            "harmony": harmony,
            "melody": melody,
            "hook": hook,
            "rhythm": rhythm,
            "arrangement": arrangement,
            "vocal": vocal,
            "mixing": mixing,
        }
        sections["hit_factor"] = build_hit_factor(sections, audio_features)
        sections["takeaway"] = build_takeaway(sections)
        sections["audio_features"] = audio_features
        sections["full_report"] = generate_full_report(sections, metadata, audio_features)
        analysis = store.save_analysis(song["id"], sections)
        export_store_snapshot(store, settings.export_path)
        return {"song": store.get_song(song["id"]), "analysis": analysis}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="ffmpeg is not installed or cannot be found on PATH.") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def build_rhythm(audio_features: dict) -> dict:
    bpm = float(audio_features.get("bpm", 0))
    density = float(audio_features.get("onset_density", 0))
    return {
        "bpm": bpm,
        "meter": "4/4",
        "groove_type": "slow ballad groove" if bpm < 85 else "midtempo pop groove" if bpm < 120 else "upbeat pop groove",
        "rhythm_density": "low" if density < 1 else "medium" if density < 3 else "high",
        "verse_rhythm_density": "medium",
        "chorus_rhythm_density": "low but sustained" if bpm < 90 else "clear and repetitive",
        "drum_intensity_curve": [1, 2, 4, 7, 9],
        "creative_principle": "Use the density contrast between verse and chorus rather than copying a reference rhythm.",
    }
