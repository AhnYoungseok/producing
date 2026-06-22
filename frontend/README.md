# Hit Song Lab Frontend

Next.js frontend for the Hit Song Lab MVP.

The primary workflow is YouTube-link-based hit song research. Users paste a YouTube link, add optional lyrics, chords, and notes, then receive a structured research profile. Uploading audio is optional and is used only when the user owns or has permission to analyze that file.

## Run

```bash
npm install
copy .env.example .env.local
npm run dev -- --port 3100
```

## Pages

- `/`: Dashboard with library statistics and recent work
- `/analyze`: YouTube-link-based hit song research and optional audio analysis
- `/library`: Song Library
- `/songs/[id]`: Hit-song research profile and analysis details
- `/patterns`: Pattern Lab
- `/hooks`: Hook Lab with lyric-hook cues, melody interval/rhythm summaries, and lyrics-source status
- `/project/new`: New Song Project
- `/composer/[project_id]`: conversational Composer Coach

## Backend dependency

The frontend expects the FastAPI backend at:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8100/api
```

If the backend is running at `127.0.0.1`, either keep the same API URL or update `.env.local` to:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8100/api
```

## Check

```bash
npm run lint
npm run build
```
