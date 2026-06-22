import math
from pathlib import Path

import librosa
import numpy as np
from scipy.signal import find_peaks

from app.services.audio_processor import load_audio

PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
STRUCTURE_NAMES = ["Intro", "Verse", "Pre-Chorus", "Chorus", "Bridge", "Final Chorus", "Outro"]


def analyze_audio(wav_path: str | Path) -> dict:
    y, sr = load_audio(wav_path)
    duration = round(float(librosa.get_duration(y=y, sr=sr)), 2)
    chroma_summary = analyze_chroma(y, sr)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
    onset_count = count_onsets(y, sr)

    audio_features = {
        "bpm": estimate_bpm(y, sr),
        "estimated_key": estimate_key_from_chroma(chroma_summary),
        "duration_seconds": duration,
        "loudness_estimate": estimate_loudness(y),
        "onset_density": round(float(onset_count / max(duration, 0.001)), 3),
        "spectral_centroid_mean": round(float(np.mean(spectral_centroid)), 2),
        "zero_crossing_rate_mean": round(float(np.mean(zero_crossing_rate)), 5),
        "chroma_summary": chroma_summary,
    }
    return {
        "audio_features": audio_features,
        "structure_estimate": estimate_structure(y, sr, duration),
    }


def estimate_bpm(y: np.ndarray, sr: int) -> float:
    hop_length = 512
    novelty = rms_novelty(y, hop_length=hop_length)
    if novelty.size < 4 or float(np.max(novelty)) <= 0:
        return 0.0
    centered = novelty - float(np.mean(novelty))
    autocorrelation = np.correlate(centered, centered, mode="full")[len(centered) - 1 :]
    min_bpm = 50
    max_bpm = 200
    min_lag = max(1, int((60 * sr) / (max_bpm * hop_length)))
    max_lag = min(len(autocorrelation) - 1, int((60 * sr) / (min_bpm * hop_length)))
    if max_lag <= min_lag:
        return 0.0
    lag_values = np.arange(min_lag, max_lag)
    weighted_scores = autocorrelation[min_lag:max_lag] / np.sqrt(lag_values)
    best_lag = min_lag + int(np.argmax(weighted_scores))
    bpm = (60 * sr) / (best_lag * hop_length)
    if bpm < 80:
        double_time_lag = max(1, best_lag // 2)
        if double_time_lag >= min_lag and autocorrelation[double_time_lag] >= autocorrelation[best_lag] * 0.35:
            bpm = (60 * sr) / (double_time_lag * hop_length)
    return round(float(bpm), 2)


def analyze_chroma(y: np.ndarray, sr: int) -> dict[str, float]:
    chroma_vector = estimate_chroma_vector(y, sr)
    return {pitch: round(float(chroma_vector[index]), 4) for index, pitch in enumerate(PITCH_CLASSES)}


def estimate_key_from_chroma(chroma_summary: dict[str, float]) -> str:
    chroma_vector = np.array([chroma_summary.get(pitch, 0.0) for pitch in PITCH_CLASSES])
    major_key, major_score = best_key_match(chroma_vector, MAJOR_PROFILE, "major")
    minor_key, minor_score = best_key_match(chroma_vector, MINOR_PROFILE, "minor")
    return major_key if major_score >= minor_score else minor_key


def estimate_loudness(y: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(np.square(y))))
    if rms <= 0:
        return -120.0
    return round(20.0 * math.log10(min(rms, 1.0)), 2)


def estimate_structure(y: np.ndarray, sr: int, duration: float) -> dict:
    if duration <= 20:
        return {
            "structure": ["Full Track"],
            "sections": [{"name": "Full Track", "start": 0.0, "end": round(duration, 2), "energy": 3}],
            "first_chorus_time": None,
            "energy_curve": [3],
            "disclaimer": "곡 구조는 오디오 특징 변화량을 바탕으로 한 자동 추정이며 실제 편곡 구조와 다를 수 있습니다.",
        }

    hop_length = 512
    rms = frame_rms(y, hop_length=hop_length)
    onset_envelope = rms_novelty(y, hop_length=hop_length)
    chroma = frame_chroma_series(y, sr, hop_length=hop_length)
    chroma_diff = align_chroma_diff(chroma, len(rms))
    frame_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    novelty = normalize_series(np.abs(np.diff(rms, prepend=rms[0])))
    novelty += normalize_series(onset_envelope[: len(novelty)])
    novelty += normalize_series(chroma_diff[: len(novelty)])
    target_section_count = min(7, max(4, int(duration // 35) + 2))
    min_gap_seconds = max(8.0, duration / (target_section_count * 2.2))
    boundary_times = select_boundaries(frame_times, novelty, target_section_count - 1, min_gap_seconds, duration)
    boundaries = [0.0, *boundary_times, duration]
    sections = []
    structure = []
    energy_curve = []

    for index, (start, end) in enumerate(zip(boundaries, boundaries[1:])):
        if end - start < 2:
            continue
        name = STRUCTURE_NAMES[min(index, len(STRUCTURE_NAMES) - 1)]
        segment = y[int(start * sr) : int(end * sr)]
        energy = int(round(min(10, max(1, estimate_segment_energy(segment)))))
        structure.append(name)
        energy_curve.append(energy)
        sections.append({"name": name, "start": round(float(start), 2), "end": round(float(end), 2), "energy": energy})

    first_chorus = next((section["start"] for section in sections if "Chorus" in section["name"]), None)
    return {
        "structure": structure,
        "sections": sections,
        "first_chorus_time": first_chorus,
        "final_chorus_expansion": "adlib + harmony + wider arrangement 후보",
        "energy_curve": energy_curve,
        "disclaimer": "곡 구조는 onset, energy, chroma 변화량을 바탕으로 한 자동 추정이며 실제 악보나 세션 구조와 다를 수 있습니다.",
    }


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    total = float(np.sum(vector))
    if total <= 0:
        return np.zeros_like(vector, dtype=float)
    return vector / total


def frame_rms(y: np.ndarray, frame_length: int = 2048, hop_length: int = 512) -> np.ndarray:
    if y.size == 0:
        return np.array([], dtype=float)
    if y.size < frame_length:
        y = np.pad(y, (0, frame_length - y.size))
    frame_count = 1 + (len(y) - frame_length) // hop_length
    if frame_count <= 0:
        return np.array([], dtype=float)
    shape = (frame_count, frame_length)
    strides = (y.strides[0] * hop_length, y.strides[0])
    frames = np.lib.stride_tricks.as_strided(y, shape=shape, strides=strides)
    return np.sqrt(np.mean(np.square(frames), axis=1))


def frame_signal(y: np.ndarray, frame_length: int = 4096, hop_length: int = 2048, max_frames: int | None = 512) -> np.ndarray:
    if y.size == 0:
        return np.empty((0, frame_length), dtype=float)
    if y.size < frame_length:
        y = np.pad(y, (0, frame_length - y.size))
    frame_count = 1 + (len(y) - frame_length) // hop_length
    shape = (frame_count, frame_length)
    strides = (y.strides[0] * hop_length, y.strides[0])
    frames = np.lib.stride_tricks.as_strided(y, shape=shape, strides=strides)
    if max_frames is not None and frame_count > max_frames:
        indices = np.linspace(0, frame_count - 1, max_frames).astype(int)
        frames = frames[indices]
    return frames


def estimate_chroma_vector(y: np.ndarray, sr: int) -> np.ndarray:
    chroma_series = frame_chroma_series(y, sr, hop_length=2048, max_frames=512)
    if chroma_series.size == 0:
        return np.zeros(12, dtype=float)
    return normalize_vector(np.mean(chroma_series, axis=1))


def frame_chroma_series(
    y: np.ndarray,
    sr: int,
    frame_length: int = 4096,
    hop_length: int = 2048,
    max_frames: int | None = 1024,
) -> np.ndarray:
    frames = frame_signal(y, frame_length=frame_length, hop_length=hop_length, max_frames=max_frames)
    if frames.size == 0:
        return np.zeros((12, 0), dtype=float)
    windowed = frames * np.hanning(frame_length)
    spectra = np.abs(np.fft.rfft(windowed, axis=1))
    frequencies = np.fft.rfftfreq(frame_length, d=1 / sr)
    valid_bins = np.where((frequencies >= 27.5) & (frequencies <= 5000))[0]
    chroma = np.zeros((12, spectra.shape[0]), dtype=float)
    for bin_index in valid_bins:
        frequency = frequencies[bin_index]
        midi_note = int(round(69 + 12 * np.log2(frequency / 440.0)))
        chroma[midi_note % 12, :] += spectra[:, bin_index]
    column_sums = np.sum(chroma, axis=0, keepdims=True)
    column_sums[column_sums <= 0] = 1.0
    return chroma / column_sums


def rms_novelty(y: np.ndarray, hop_length: int = 512) -> np.ndarray:
    rms = frame_rms(y, hop_length=hop_length)
    if rms.size == 0:
        return np.array([], dtype=float)
    return np.maximum(0, np.diff(rms, prepend=rms[0]))


def count_onsets(y: np.ndarray, sr: int = 22050, hop_length: int = 512) -> int:
    novelty = rms_novelty(y, hop_length=hop_length)
    if novelty.size == 0 or float(np.max(novelty)) <= 0:
        return 0
    threshold = float(np.mean(novelty) + np.std(novelty))
    min_distance = max(1, int((sr / hop_length) * 0.08))
    peaks, _ = find_peaks(novelty, height=threshold, distance=min_distance)
    return int(len(peaks))


def normalize_series(series: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(series))) if series.size else 0.0
    if peak <= 0:
        return np.zeros_like(series, dtype=float)
    return series / peak


def best_key_match(chroma_vector: np.ndarray, profile: np.ndarray, mode: str) -> tuple[str, float]:
    normalized_chroma = normalize_vector(chroma_vector)
    normalized_profile = normalize_vector(profile)
    best_index = 0
    best_score = -1.0
    for index in range(12):
        score = cosine_similarity(normalized_chroma, np.roll(normalized_profile, index))
        if score > best_score:
            best_index = index
            best_score = score
    return f"{PITCH_CLASSES[best_index]} {mode}", best_score


def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator == 0:
        return 0.0
    return float(np.dot(left, right) / denominator)


def select_boundaries(frame_times: np.ndarray, novelty: np.ndarray, max_boundaries: int, min_gap_seconds: float, duration: float) -> list[float]:
    ranked_indices = np.argsort(novelty)[::-1]
    selected: list[float] = []
    for index in ranked_indices:
        boundary_time = float(frame_times[index])
        if boundary_time < 5 or duration - boundary_time < 5:
            continue
        if all(abs(boundary_time - existing) >= min_gap_seconds for existing in selected):
            selected.append(boundary_time)
        if len(selected) >= max_boundaries:
            break
    if len(selected) < max_boundaries:
        interval = duration / (max_boundaries + 1)
        for boundary_index in range(1, max_boundaries + 1):
            boundary_time = interval * boundary_index
            if all(abs(boundary_time - existing) >= min_gap_seconds * 0.6 for existing in selected):
                selected.append(boundary_time)
            if len(selected) >= max_boundaries:
                break
    return sorted(round(time, 2) for time in selected)


def align_chroma_diff(chroma: np.ndarray, target_length: int) -> np.ndarray:
    if chroma.shape[1] == 0:
        return np.zeros(target_length)
    if chroma.shape[1] != target_length:
        source_x = np.linspace(0, 1, chroma.shape[1])
        target_x = np.linspace(0, 1, target_length)
        chroma = np.vstack([np.interp(target_x, source_x, chroma_row) for chroma_row in chroma])
    return np.mean(np.abs(np.diff(chroma, axis=1, prepend=chroma[:, :1])), axis=0)


def estimate_segment_energy(segment: np.ndarray) -> float:
    if segment.size == 0:
        return 1.0
    rms = float(np.sqrt(np.mean(np.square(segment))))
    return 1 + min(9, rms * 80)
