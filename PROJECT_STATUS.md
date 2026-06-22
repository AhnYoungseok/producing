# Project Status

Last reviewed: 2026-06-22

## Summary

Hit Song Lab is a local full-stack MVP for YouTube/reference-song-based hit-song research. It stores reference-song features, summarizes producer-style patterns, and uses the accumulated library as source material for original-song planning.

The app does not download, extract, capture, separate, convert, or analyze YouTube audio. YouTube links are used as reference metadata/search starting points only. Signal analysis is reserved for user-owned or permitted uploaded audio files.

## Current Structure

- `frontend/`: Next.js, TypeScript, Tailwind CSS UI.
- `backend/`: FastAPI, SQLite, analysis services, local storage, tests.
- `backend/data/`: local SQLite database. Ignored by git.
- `backend/exports/hit_song_library/`: generated CSV/JSON exports by genre. Ignored or treated as runtime output.
- `backend/seeds/cloud_reference_queue.json`: initial curated real-song reference queue.
- `backend/app/services/curated_reference_catalog.py`: additional curated real-song catalog for local auto batching.
- `docs/`: project design notes.
- `sample_data/`: portable example data structures.
- `.github/workflows/`: cloud batch workflow scaffolding.

## Implemented Features

- Dashboard with song counts, charts, pattern summaries, and analyzed song-title list.
- YouTube Reference Analysis form.
- Optional user-owned audio upload path for signal analysis.
- Song Library list and song detail pages.
- Producer-style report sections: concept, structure, harmony, melody/hook, lyrics, rhythm, arrangement, vocal, mixing, hit points, creative application, data confidence.
- Hook Lab page with lyric-hook cues, melody interval/rhythm summaries, hook locations, and lyrics-source status.
- User-provided lyrics/chords/notes update flow on song detail pages.
- Pattern Lab and Composer Coach MVP flow.
- SQLite persistence.
- Local CSV/JSON export.
- Automatic local reference-song batch worker:
  - default: enabled
  - adds 10 unique curated real hit songs on backend startup
  - adds 10 more every 600 seconds while backend is running

## Current Local Data State

At review time, the local database had grown beyond the original seed set through the auto batch worker. The count may change while the backend is running because `AUTO_REFERENCE_BATCH_ENABLED=true` by default.

Check current count:

```powershell
cd "D:\새 폴더\hit-song-lab"
backend\.venv\Scripts\python.exe - <<'PY'
import sqlite3
con = sqlite3.connect("backend/data/hit_song_lab.db")
print(con.execute("select count(*) from songs").fetchone()[0])
PY
```

PowerShell may not support the heredoc form above in every shell host. A simpler check is to open the dashboard or call:

```powershell
Invoke-RestMethod http://127.0.0.1:8100/api/library/dashboard
```

## Run

Backend:

```powershell
cd "D:\새 폴더\hit-song-lab\backend"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8100
```

Frontend:

```powershell
cd "D:\새 폴더\hit-song-lab\frontend"
npm install
copy .env.example .env.local
npm run dev -- --port 3100
```

Open:

```text
http://127.0.0.1:3100
```

## Test

Backend:

```powershell
cd "D:\새 폴더\hit-song-lab\backend"
$env:AUTO_REFERENCE_BATCH_ENABLED="false"
.venv\Scripts\python.exe -m pytest
```

Frontend:

```powershell
cd "D:\새 폴더\hit-song-lab\frontend"
npm run lint
npm run build
```

## Known Incomplete Areas

- Full lyrics are not automatically collected or stored. Users must provide lyrics themselves.
- Chord data is curated/user-provided/inferred, not automatically transcribed from YouTube audio.
- Melody hook intervals are summarized as research notes, not score-level transcription.
- Auto batching runs only while the local backend and PC are on.
- Google Sheets cloud sync needs credentials and workflow setup.
- Hook Lab currently loads analyses per song; this should be optimized before very large libraries.
- Public music database integrations are MVP-level and optional.

## Current Risks

- Auto batch on startup can grow the DB unexpectedly if left enabled.
- Running tests without disabling auto batch may mutate the local database.
- Real lyrics and melody transcriptions must be handled carefully to avoid copyright problems.
- This local folder is not guaranteed to be a git repository unless initialized/pushed separately.
