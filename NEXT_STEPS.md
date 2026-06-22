# Next Steps

## Start Here

1. Confirm backend is running:

```powershell
Invoke-RestMethod http://127.0.0.1:8100/api/health
```

2. Confirm frontend is running:

```text
http://127.0.0.1:3100
```

3. Check auto batch status:

```powershell
Invoke-RestMethod http://127.0.0.1:8100/api/research/auto-batch/status
```

## Recommended Commands

Backend:

```powershell
cd "D:\새 폴더\hit-song-lab\backend"
.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8100
```

Frontend:

```powershell
cd "D:\새 폴더\hit-song-lab\frontend"
npm run dev -- --port 3100
```

Run checks:

```powershell
cd "D:\새 폴더\hit-song-lab\backend"
$env:AUTO_REFERENCE_BATCH_ENABLED="false"
.venv\Scripts\python.exe -m pytest

cd "D:\새 폴더\hit-song-lab\frontend"
npm run lint
npm run build
```

Export local library:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8100/api/library/export
```

## Next Development Recommendation

Build a single backend endpoint for Hook Lab summaries:

```text
GET /api/library/hook-summaries
```

It should return:

- song id
- title
- artist
- genre
- hook cue
- hook type
- hook location
- melody interval summary
- melody rhythm summary
- lyrics-source status
- confidence

This will make Hook Lab fast enough for 1,000+ songs.

## Suggested Prompt for Codex

```text
Continue Hit Song Lab from the current repo.

First, read PROJECT_STATUS.md, TODO.md, ISSUES.md, NEXT_STEPS.md, and docs/analysis_schema.md.

Implement the next Priority 1 item:
Add GET /api/library/hook-summaries so Hook Lab no longer fetches every song analysis one by one.

Keep YouTube audio extraction forbidden.
Do not add full copyrighted lyrics.
Run backend tests with AUTO_REFERENCE_BATCH_ENABLED=false and run frontend lint/build.
Update CHANGELOG.md when done.
```
