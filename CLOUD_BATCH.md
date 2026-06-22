# Hit Song Lab Cloud Batch

This runbook explains how to keep Hit Song Lab accumulating reference-song data even when the local PC is turned off.

## Why This Is Needed

The local Codex heartbeat can run only while the PC and local Codex workspace are available. If the PC is powered off, local SQLite, local files, and the local browser cannot keep running.

For always-on operation, use GitHub Actions as the scheduler and Google Sheets as the cloud ledger.

## Prepared Files

```text
.github/workflows/hit-song-lab-cloud-batch.yml
backend/scripts/cloud_hit_song_batch.py
backend/seeds/cloud_reference_queue.json
backend/requirements-cloud.txt
```

## What The Batch Does

1. Runs every 10 minutes in GitHub Actions.
2. Reads the Google Sheet `Song Library` tab.
3. Normalizes title + artist and skips duplicates.
4. Adds exactly 10 unique real hit-song reference profiles from `backend/seeds/cloud_reference_queue.json`.
5. Updates these tabs:
   - `Song Library`
   - `전체 곡명`
   - `후크 멜로디 리듬`
   - `Chord Lyrics`
   - `Producer Features`
   - `Dashboard`
   - `Statistics`
   - `Genre Summary`
   - `Pattern Summaries`
   - date-based `YYYY.M.D 추천 정보`
6. Uses YouTube links only as reference/search metadata.

## Safety Policy

The cloud batch does not download, extract, convert, capture, separate, or analyze YouTube audio.

It stores only reference metadata, concise lyric/theme summaries, hook research notes, chord/structure fields, confidence labels, and producer takeaways. It does not store full copyrighted lyrics.

## Required GitHub Secrets

Set these in the GitHub repository:

```text
GOOGLE_SHEET_ID=1U_WUMnel9AZv-7YymqMRMDw5iX_MI-M3r2Yw0e7umNs
GOOGLE_SERVICE_ACCOUNT_JSON=<full Google service account JSON>
```

## Google Sheet Permission Setup

1. Create a Google Cloud service account.
2. Enable Google Sheets API.
3. Create a JSON key for the service account.
4. Share the target Google Sheet with the service account email as an editor.
5. Paste the full JSON key into the GitHub secret `GOOGLE_SERVICE_ACCOUNT_JSON`.

## Manual Dry Run

```bash
python backend/scripts/cloud_hit_song_batch.py --dry-run --batch-size 10
```

## Manual Real Run

```bash
python backend/scripts/cloud_hit_song_batch.py --batch-size 10
```

## Important Limitations

- This cloud batch updates Google Sheets, not the local SQLite DB, while the PC is off.
- The local SQLite database can only be updated when the PC or a deployed database is available.
- To fully sync the local app after the PC turns back on, add a Google Sheet to SQLite import step.
- The current queue has a finite number of curated real songs. Add more real hit songs to `backend/seeds/cloud_reference_queue.json` before the queue runs out.
