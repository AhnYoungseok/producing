# Changelog

## 2026-06-28

### Fixed

- Rebuilt Composer Coach concept flow around structured archetypes, reset support, concept-aware reference matching, and harmony briefs that vary from the matched reference statistics.
- Changed the default auto-reference batch settings to safe development defaults: disabled and no startup run unless explicitly enabled by environment variables.
- Replaced broken Hook Lab UI copy and backend Hook Lab fallback strings so loading, error, empty, search, filter, confidence, and pagination states are readable.
- Replaced the frontend API fallback error message with a stable readable message.
- Updated stale project docs that still described Hook Lab as per-song analysis fetching and auto batch as enabled by default.

### Added

- Added an `AI 5-axis analysis draft` action to public reference cards, filling missing lyric-structure, melody, rhythm/groove, chord, and accompaniment/production analysis fields from available metadata while preserving user-entered values.
- Added public-site reference-song analysis panels for the three required core fields: chorus/hook lyric excerpt, chord progression analysis, and hook melody analysis.
- Added local public-site editing for chorus/hook excerpts, lyric source/input/permission/visibility/confidence metadata, section chord progressions, Roman numeral conversion, harmonic interpretation, and hook melody summaries.
- Expanded the public-site required analysis model from 3 fields to 5 creative axes: lyrics, melody, rhythm/groove, chord progression, and accompaniment/production method.
- Added Composer Coach hook-melody sketches directly under the lyric hook examples, with three generated contour/rhythm variants and browser Web Audio playback for quick auditioning.
- Added `POST /api/composer/{project_id}/reset` to restart the Composer Coach concept flow without manually editing the database.
- Added and tested the bulk Hook Lab summary response shape for `GET /api/library/hook-summaries`, including country, year, BPM, key, hook cue/type/location, melody summaries, lyrics source status, confidence, and updated timestamps.
- Added a Hook Lab endpoint structure test for the bulk summary payload.
- Added Hook Lab client-side search, genre filtering, confidence filtering, pagination, selected-reference count, and direct YouTube search links.
- Added recommendation harmony statistics so Composer Coach can use selected/recommended songs' verse, pre-chorus, chorus, and bridge progressions instead of repeating a fixed fallback.

### Changed

- Optimized public-site concept selection so button state updates immediately while heavy recommendation and brief regeneration are debounced and cached.
- Moved the concept reset button to the top of the concept section and the brief reset button to the top of the creation brief section.
- Updated the public-site concept label to the softer `감성 / 말투`.
- Changed lyric analysis completion so structure-only analysis can count as analyzed while still showing that the original chorus/hook text must be manually verified before any excerpt is displayed.
- Upgraded the public-site concept finder from a single coarse persona label into an 8-axis visual persona model with detailed subtype codes, coordinate map, score bars, rationale notes, and nearest archetype ranking.
- Strengthened source-safe harmony, melody, and hook analyzers so user-provided chords/lyrics produce detailed section functions, tension/release notes, reharmonization options, hook design, melody contour/rhythm summaries, and explicit confidence/source labels without using YouTube audio extraction.
- Updated Hook Lab so it loads reference summaries through one bulk API call instead of relying on per-song analysis requests.
- Expanded confidence metadata for local and cloud/ledger hook summaries while preserving legacy field names for compatibility.
- Reworked Composer Coach so the creation brief is the most prominent section, with practical concept, structure, harmony, hook, arrangement, vocal, and plagiarism-prevention guidance.
- Updated Composer Coach harmony options and the creation brief to prioritize reference-song chord statistics, then transform them with slash chords, secondary dominants, modal interchange, sus/add9 voicings, and new bass motion.
- Changed the public-site harmony brief generator so it selects distinct harmony palettes from concept axes, sound lane, BPM/genre signals, and available chord samples instead of repeating one fixed G major / E minor fallback.
- Added K-pop/global groove harmony detection so Korean pop hooks, post-chorus/performance hooks, drum grooves, and bass/synth references produce dedicated F/D minor or Ab/F minor progression plans instead of falling back to the generic ballad template.
- Added per-reference chord progression analysis to the public-site brief and song detail cards, including raw chord availability, functional family, confidence/source status, and a transformed new-song progression for each recommended song.
- Removed age/speaker-based concept categorization from the public-site concept picker and brief copy; concept selection now starts from speaking position, viewpoint, tone, attitude, emotion, situation, and sound.
- Made the public-site persona graph interactive: dragging the center point now adjusts concept/emotion axes, persists the adjustment, and recalculates archetype, recommended songs, and creation brief around the new coordinates.
- Updated the public-site creation brief so recommended-song chorus/hook lyric status, per-section chord/Roman analysis, and hook melody status are reflected in the concept brief and statistics.
- Updated public-site reference cards and briefs to show missing rhythm and accompaniment/production analysis explicitly instead of treating them as optional notes.
- Replaced broken Korean UI copy in Hook Lab and Composer Coach with clear Korean workflow/status text.

### Verified

- Backend tests passed with `AUTO_REFERENCE_BATCH_ENABLED=false`: 27 tests.
- Backend tests passed with `AUTO_REFERENCE_BATCH_ENABLED=false`: 28 tests after Composer reset/concept updates.
- Frontend `npm run lint` passed.
- Frontend `npm run build` passed.
- FastAPI server started successfully on port 8110 with auto batch disabled.
- HTTP checks passed for `/docs`, `/api/research/auto-batch/status`, `/api/library/hook-summaries`, bad song ID 404, and main frontend routes.

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
- Older note: this folder was previously not initialized as a git repository. It is now on branch `main` in the checked workspace.
