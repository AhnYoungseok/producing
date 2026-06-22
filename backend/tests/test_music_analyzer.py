import numpy as np

from app.services.music_analyzer import analyze_chroma, estimate_bpm, estimate_key_from_chroma, estimate_loudness


def test_estimate_bpm_from_click_track() -> None:
    sr = 22050
    duration = 8
    y = np.zeros(duration * sr)
    for sample_index in range(0, duration * sr, sr // 2):
        y[sample_index : sample_index + 128] = 1.0

    bpm = estimate_bpm(y, sr)

    assert 110 <= bpm <= 130


def test_chroma_and_key_for_a_tone() -> None:
    sr = 22050
    t = np.linspace(0, 2, sr * 2, endpoint=False)
    y = np.sin(2 * np.pi * 440 * t)
    chroma = analyze_chroma(y, sr)

    assert set(chroma.keys()) == {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"}
    assert chroma["A"] > 0.5


def test_estimate_key_from_c_major_chroma() -> None:
    chroma = {"C": 0.34, "C#": 0.01, "D": 0.02, "D#": 0.01, "E": 0.25, "F": 0.02, "F#": 0.01, "G": 0.29, "G#": 0.01, "A": 0.02, "A#": 0.01, "B": 0.01}

    assert estimate_key_from_chroma(chroma) == "C major"


def test_estimate_loudness_handles_silence() -> None:
    assert estimate_loudness(np.zeros(1024)) == -120.0
