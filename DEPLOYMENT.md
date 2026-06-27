# Hit Song Lab Deployment

This project is designed to run from GitHub while the local PC is off.

## Target Architecture

- GitHub Actions: adds 10 reference songs every 10 minutes.
- Google Sheets: primary spreadsheet mirror when service-account secrets are configured.
- Render: always-on FastAPI backend.
- Vercel: Next.js frontend.

GitHub Actions already writes `cloud_ledger/song_library.json`. The deployed backend reads that ledger by default. When Google credentials are configured, it can read the Google Sheet directly by setting `CLOUD_LIBRARY_SOURCE=google_sheet`.

## 1. Google Sheet Secrets

In GitHub repo settings, add:

```text
GOOGLE_SHEET_ID=1U_WUMnel9AZv-7YymqMRMDw5iX_MI-M3r2Yw0e7umNs
GOOGLE_SERVICE_ACCOUNT_JSON=<full service account JSON>
```

Share the Google Sheet with the service account `client_email` as an editor.

## 2. Backend On Render

Create a Render Blueprint from this GitHub repository:

```text
https://github.com/AhnYoungseok/producing
```

Render uses `render.yaml` from the repository root.

After the service is created, set these environment variables:

```text
FRONTEND_ORIGIN=<your Vercel frontend URL>
FRONTEND_ORIGINS=<your Vercel frontend URL>,http://localhost:3100
GOOGLE_SERVICE_ACCOUNT_JSON=<full service account JSON>
```

Default backend data mode:

```text
CLOUD_LIBRARY_SOURCE=cloud_ledger
```

To read the spreadsheet directly:

```text
CLOUD_LIBRARY_SOURCE=google_sheet
```

Keep these off on Render because GitHub Actions owns scheduled accumulation:

```text
AUTO_REFERENCE_BATCH_ENABLED=false
AUTO_REFERENCE_BATCH_RUN_ON_STARTUP=false
```

## 3. Frontend On Vercel

Import the same GitHub repository into Vercel.

Use:

```text
Root Directory: frontend
Framework Preset: Next.js
Build Command: npm run build
Install Command: npm install
```

Set:

```text
NEXT_PUBLIC_API_BASE_URL=https://<your-render-service>.onrender.com/api
```

## 4. Check URLs

Backend health:

```text
https://<your-render-service>.onrender.com/api/health
```

Frontend:

```text
https://<your-vercel-project>.vercel.app/hooks
```

GitHub Actions:

```text
https://github.com/AhnYoungseok/producing/actions
```

Cloud ledger:

```text
https://github.com/AhnYoungseok/producing/blob/main/cloud_ledger/song_library.json
```

## Notes

Render free instances may sleep. For truly always-on behavior, use an always-on Render instance type.

GitHub scheduled workflows can be delayed by GitHub load, but they do not require the local PC to be powered on.
