# TODO

## Priority 1: Must Do

- Add a clear backend startup banner or dashboard notice when auto batch is enabled.
- Add a bulk API for song analyses so Hook Lab does not request one analysis per song.
- Add a simple duplicate-audit command/API using normalized title + artist.
- Add an export button or scheduled export that clearly includes the current timestamp.
- Add tests for `reference_batch_importer` and `auto_reference_batch_worker`.
- Document how to turn auto batching off before tests or classroom demos.
- Decide whether local runtime DB files should be copied to a shared Google Sheet, GitHub artifact, or both.
- Add a stable backup/export command before large batch runs.

## Priority 2: Good Improvements

- Add a dedicated Admin/Settings page for:
  - auto batch enabled/disabled
  - batch interval
  - remaining candidate count
  - last 10 added songs
  - manual export
- Add inline editing for curated song fields.
- Add confidence badges per field in Song Detail and Hook Lab.
- Add chart filters by genre, country, decade, BPM range, and hook type.
- Add a better lyrics workflow:
  - user-provided lyrics only
  - official lyrics search link
  - section parser
  - short hook-cue extraction
- Add school-PC setup script for Windows.
- Add GitHub setup instructions and optional GitHub Actions workflow guide.

## Priority 3: Later

- Connect licensed/allowed music APIs for stronger metadata.
- Add a proper PostgreSQL adapter while keeping SQLite for MVP.
- Add user accounts and project-level libraries.
- Add PDF report export.
- Add interactive code progression visualization.
- Add melody contour charting from user-provided MIDI/score or permitted audio.
- Add stem separation only for user-owned/permitted audio, not YouTube.
- Add K-pop Ballad, Global Pop, Dance Pop, Hip-hop, Rock specialized analysis modes.
- Add a guided Composer Coach workflow that updates the blueprint card after each chat turn.
