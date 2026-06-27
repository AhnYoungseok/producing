# Hit Song Lab Deployment

This project is designed to run from GitHub while the local PC is off.

## Target Architecture

- GitHub Actions: adds 10 reference songs every 10 minutes.
- GitHub Pages: always-on browser dashboard.
- Google Sheets: primary spreadsheet mirror when service-account secrets are configured.
- Render: optional FastAPI backend for the full local-style app.
- Vercel: optional Next.js frontend for the full local-style app.

GitHub Actions already writes `cloud_ledger/song_library.json`. The GitHub Pages dashboard reads that ledger directly, so the public viewer does not need a running PC, Render instance, or Vercel deployment. When Google credentials are configured, the workflow also mirrors the same accumulated data into Google Sheets.

## 1. Always-On Browser Dashboard

Zero-settings URL that works without enabling GitHub Pages:

```text
https://cdn.jsdelivr.net/gh/AhnYoungseok/producing@main/public-site/index.html
```

GitHub Pages URL after Pages is enabled:

```text
https://ahnyoungseok.github.io/producing/
```

The dashboard is deployed by `.github/workflows/pages.yml` from `public-site/`.

It shows:

- accumulated total count
- public cloud song rows
- baseline local DB count
- added date beside each song
- genre, hook, and BPM summary charts

If the GitHub Pages URL does not open after the first push, enable GitHub Pages once:

```text
Repository Settings > Pages > Source: GitHub Actions
```

The jsDelivr URL above does not require that setting. After either URL is available, no local PC process is required for the browser dashboard.

## 2. Google Sheet Secrets

In GitHub repo settings, add:

```text
GOOGLE_SHEET_ID=1U_WUMnel9AZv-7YymqMRMDw5iX_MI-M3r2Yw0e7umNs
GOOGLE_SERVICE_ACCOUNT_JSON=<full service account JSON>
```

Share the Google Sheet with the service account `client_email` as an editor.

Without these secrets, GitHub Actions still accumulates `cloud_ledger/song_library.json`, but the spreadsheet mirror cannot update.

## 3. Optional Backend On Render

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

## 4. Optional Frontend On Vercel

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

## 5. Check URLs

Always-on GitHub Pages viewer:

```text
https://ahnyoungseok.github.io/producing/
```

Zero-settings GitHub CDN viewer:

```text
https://cdn.jsdelivr.net/gh/AhnYoungseok/producing@main/public-site/index.html
```

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
