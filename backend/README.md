# Hit Song Lab Backend

FastAPI backend for YouTube-link-based hit song research, optional user-owned audio analysis, pattern mining, and new song blueprint generation.

The backend never downloads, extracts, separates, converts, or analyzes YouTube audio. YouTube links are used only for allowed metadata and reference context.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8100
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8100
```

## Environment

The most important local settings are:

```bash
DATABASE_URL=sqlite:///./data/hit_song_lab.db
EXPORT_DIR=./exports/hit_song_library
FRONTEND_ORIGIN=http://localhost:3100
AUTO_REFERENCE_BATCH_ENABLED=true
AUTO_REFERENCE_BATCH_INTERVAL_SECONDS=600
AUTO_REFERENCE_BATCH_SIZE=10
AUTO_REFERENCE_BATCH_RUN_ON_STARTUP=true
```

Set `AUTO_REFERENCE_BATCH_ENABLED=false` before tests or when you do not want the local database to grow automatically.

## Main Endpoints

- `POST /api/research/youtube`: create a hit-song research profile from a YouTube link, public metadata, user lyrics, chords, and notes
- `POST /api/research/next-reference-batch`: add the next unique curated reference-song batch
- `GET /api/research/auto-batch/status`: inspect the automatic 10-song batch worker
- `POST /api/research/auto-batch/run-now`: run one 10-song batch immediately
- `POST /api/analyze`: analyze an uploaded audio file owned or permitted by the user
- `GET /api/songs`: list saved songs
- `GET /api/library/statistics`: aggregate saved hit-song data
- `POST /api/library/export`: write accumulated song data to genre-based CSV/JSON files under `exports/hit_song_library`
- `POST /api/patterns/extract`: extract shared patterns from selected songs
- `POST /api/projects/{project_id}/blueprint`: generate a new song blueprint

## Optional Public Data Providers

```bash
LASTFM_API_KEY=
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
```

MusicBrainz lookup works without an API key.

## Test

```bash
set AUTO_REFERENCE_BATCH_ENABLED=false
.venv\Scripts\python.exe -m pytest
```

Use `python -m pytest` inside the virtual environment so `pydantic-settings`, `librosa`, and the pinned dependencies are available.
