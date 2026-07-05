# Antibody browser extension (MVP)

Check suspicious text against Antibody's shared scam-pattern graph without leaving
your browser. It calls the **read-only `/scan`** endpoint, so a quick check never
records a report or touches the shared graph.

## What it does

- **Popup** — paste text and check it, or scan the current page's visible text.
- **Right-click** — select text on any page → *"Check … with Antibody"* → a
  desktop notification with the verdict.
- Read-only by design: scanning never contributes to the shared memory.

## Load it (Chrome / Edge, unpacked)

1. Open `chrome://extensions` (or `edge://extensions`).
2. Toggle **Developer mode** on.
3. Click **Load unpacked** and select this `extension/` folder.
4. Pin the Antibody icon and click it, or select text and right-click.

## Backend

By default it talks to the live demo
(`https://antibody-251148844884.asia-south1.run.app`). To use a local backend,
set `API_BASE` in [`background.js`](background.js) to `http://127.0.0.1:8000`
(already allowlisted in [`manifest.json`](manifest.json)) and run
`uvicorn api.main:app` locally.

Requests are made from the background service worker, which has `host_permissions`
for the API origin, so they aren't subject to page CORS.
