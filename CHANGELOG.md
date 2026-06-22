# Changelog

## 2026-06-22

### Added

- Added automatic local reference-song batch worker.
- Added curated real-hit-song catalog for continued 10-song batches after the initial queue is exhausted.
- Added Hook Lab auto-batch status panel.
- Added Hook Lab lyrics-source status column.
- Added song-detail lyrics display card for user-provided lyrics.
- Added support for updating lyrics/chords/notes on curated reference-song profiles.
- Added a Billboard chart ingestion script that prepends current Hot 100 and Korea Global K-Songs references to the safe local queue.
- Added project documentation:
  - `PROJECT_STATUS.md`
  - `TODO.md`
  - `ISSUES.md`
  - `NEXT_STEPS.md`
  - `docs/analysis_schema.md`
  - `sample_data/songs.json`

### Changed

- Updated root README with current environment variables, auto-batch behavior, and current documentation map.
- Updated backend README with auto-batch settings and safer test command.
- Updated frontend README with Hook Lab route and backend URL notes.
- Preserved existing BPM/Key/public metadata fields when a user updates lyrics/chords on curated profiles.
- Expanded `backend/seeds/cloud_reference_queue.json` with additional real domestic and international hit-song reference profiles so the 10-minute auto-batch worker can continue after the first local queue is exhausted.
- Prepended current Billboard Hot 100 and Billboard Korea Global K-Songs candidates to the reference queue with chart rank/source metadata and low-confidence musical fields where public metadata was not available.

### Verified

- Backend Python compile check passed for modified modules.
- Backend test suite passed: 25 tests.
- Frontend `npm run lint` passed.
- Frontend `npm run build` passed.

### Notes

- Automatic lyrics collection was not added. Full lyrics must be user-provided.
- YouTube audio extraction remains explicitly unsupported and forbidden.
- The current folder is not initialized as a git repository; `git status` reports that there is no `.git` directory.
