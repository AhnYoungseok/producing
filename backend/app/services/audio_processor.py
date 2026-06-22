import subprocess
from pathlib import Path
from typing import Protocol

import librosa
import numpy as np
from fastapi import UploadFile

from app.core.config import settings

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a"}


class AsyncUpload(Protocol):
    filename: str | None

    async def read(self, size: int = -1) -> bytes:
        ...


def validate_audio_file_name(file_name: str | None) -> str:
    if not file_name:
        raise ValueError("오디오 파일을 선택해 주세요.")
    safe_name = Path(file_name).name
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValueError("지원하지 않는 파일 형식입니다. MP3, WAV, M4A 파일만 업로드할 수 있습니다.")
    return safe_name


async def save_upload_file(
    file: UploadFile | AsyncUpload,
    storage_root: Path,
    song_id: str,
    max_size_bytes: int = settings.max_upload_bytes,
) -> Path:
    safe_name = validate_audio_file_name(file.filename)
    target_dir = storage_root / song_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / safe_name
    total_size = 0

    with target_path.open("wb") as output:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > max_size_bytes:
                output.close()
                target_path.unlink(missing_ok=True)
                raise ValueError("파일 크기는 MVP 기준 50MB를 초과할 수 없습니다.")
            output.write(chunk)

    if total_size == 0:
        target_path.unlink(missing_ok=True)
        raise ValueError("업로드된 파일이 비어 있습니다.")

    return target_path


def convert_to_wav(input_path: str | Path, output_dir: str | Path | None = None) -> Path:
    source = Path(input_path)
    target_dir = Path(output_dir) if output_dir else source.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    wav_path = target_dir / "analysis.wav"

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-ac",
        "1",
        "-ar",
        str(settings.audio_sample_rate),
        str(wav_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg WAV 변환에 실패했습니다: {result.stderr.strip()}")
    return wav_path


def load_audio(wav_path: str | Path) -> tuple[np.ndarray, int]:
    y, sample_rate = librosa.load(Path(wav_path), sr=settings.audio_sample_rate, mono=True)
    if y.size == 0:
        raise ValueError("변환된 오디오에서 분석 가능한 샘플을 찾지 못했습니다.")
    return y, sample_rate
