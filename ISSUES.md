# Issues and Risks

Last reviewed: 2026-06-22

## Found Issues

1. Auto batch can mutate the local database during development.
   - Current default: enabled.
   - Impact: DB count changes after backend startup and every 10 minutes.
   - Workaround: set `AUTO_REFERENCE_BATCH_ENABLED=false` in `backend/.env` before tests or demos.

2. Hook Lab does many requests for large libraries.
   - Current behavior: fetches songs, then fetches each analysis separately.
   - Impact: will become slow at hundreds or thousands of songs.
   - Fix: add a backend endpoint like `GET /api/songs/analyses` or include analysis summaries in `/api/songs`.

3. Full lyrics are not automatically shown.
   - Reason: the app must not automatically collect/store copyrighted lyrics.
   - Current safe workflow: user provides lyrics manually, then the app displays and analyzes that user-provided text.

4. Chord and melody data are not guaranteed ground truth.
   - Source: curated notes, user input, public metadata, or low/medium-confidence inference.
   - Fix: add Data Confidence visibly everywhere and prefer user-verified chords.

5. Google Sheets integration is not fully automatic on every local click.
   - Existing cloud script requires Google service account credentials.
   - Local app currently focuses on SQLite and CSV/JSON export.

6. Root folder may not be initialized as a git repository.
   - `git status` previously failed in this workspace.
   - Fix: initialize git or clone/push to a GitHub repository intentionally.

## Security Notes

- Do not commit `.env`, API keys, Google service account JSON, SQLite runtime DBs, uploaded audio, or local logs.
- Keep `.gitignore` active for:
  - `backend/.env`
  - `backend/data/`
  - `backend/storage/`
  - `frontend/.env.local`
  - `frontend/node_modules/`
  - `frontend/.next/`
- Optional API keys:
  - `LASTFM_API_KEY`
  - `SPOTIFY_CLIENT_ID`
  - `SPOTIFY_CLIENT_SECRET`

## Copyright and YouTube Notes

- Do not implement YouTube audio downloading, extraction, hidden capture, stream ripping, audio separation, or conversion.
- Do not add `yt-dlp`, `youtube-dl`, or similar packages.
- YouTube URLs are metadata/reference/search starting points only.
- Signal analysis must use user-owned or permitted uploaded audio.
- Do not store full copyrighted lyrics automatically.
- Do not store full melody transcriptions automatically.
- Keep hook cues short and non-reconstructive.
- Original-song advice must generalize creative principles instead of copying lyrics, melody, riffs, or sound signatures.

## Data Quality Risks

- Curated catalog entries are educational research scaffolds and may need verification.
- BPM/Key/chord fields can be medium or low confidence unless sourced from a reliable API or user-provided verified data.
- Some auto-batch entries are summarized by genre heuristics; they should be reviewed before being treated as final analysis.
