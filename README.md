# Email App

Self-hosted desktop app for composing and bulk-sending personalised emails via your own SMTP credentials. Runs entirely on your machine — no cloud, no subscriptions.

## Features

- **Compose** — rich-text HTML editor (TipTap), attachments, reply-to
- **Bulk send** — CSV mail-merge with `{{placeholder}}` syntax, per-minute / per-hour rate limiting, live progress
- **Templates** — reusable subjects + bodies with preview rendering
- **Contacts** — import via CSV, search, groups
- **Send logs** — per-recipient status, one-click retry on failures
- **SMTP** — any SMTP provider (Gmail App Password, SES, Postmark, Mailpit, etc.), credentials Fernet-encrypted at rest

## Tech stack

| Layer | Technology |
|---|---|
| Desktop shell | pywebview (WKWebView / WebView2 / WebKitGTK) |
| Backend | FastAPI + uvicorn (in-process thread) |
| Database | SQLite (WAL mode) via SQLAlchemy async + Alembic |
| Frontend | React 19 + Vite + TypeScript + Tailwind v4 + TanStack Query |

## Requirements

- Python 3.13+
- Node 18+ / npm
- `uv` — [install](https://docs.astral.sh/uv/getting-started/installation/)
- macOS: nothing extra (WKWebView built-in)
- Windows: WebView2 runtime (ships with Windows 11; [download](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) for Windows 10)
- Linux: `libwebkit2gtk-4.1` — `sudo apt install libwebkit2gtk-4.1-dev`

## Quick start

```bash
# 1. Clone + install Python deps
uv sync

# 2. Build frontend
cd frontend && npm install && npm run build && cd ..

# 3. Launch
make gui
```

First launch creates `~/Library/Application Support/EmailApp/` (macOS) with the SQLite DB, Fernet key, and attachments directory.

## Dev mode

Run backend and frontend separately for hot-reload:

```bash
# Terminal 1 — FastAPI on :8765
make headless

# Terminal 2 — Vite dev server on :5173
cd frontend && npm run dev

# Terminal 3 — open pywebview pointing at Vite
EMAIL_APP_DEV=1 VITE_API_TARGET=http://127.0.0.1:8765 make gui
```

## SMTP setup

### Gmail
- Host: `smtp.gmail.com` · Port: `587` · STARTTLS
- Requires an [App Password](https://support.google.com/accounts/answer/185833) (not your account password)

### Mailpit (local dev / testing)
```bash
docker run -p 1025:1025 -p 8025:8025 axllent/mailpit
```
- Host: `localhost` · Port: `1025` · No TLS
- Web UI: `http://localhost:8025`

### SES / Postmark / Resend
Use their SMTP bridge credentials. Residential IPs without SPF/DKIM/DMARC will land in spam — use a transactional provider for real volume.

## CSV format

```csv
email,first_name,last_name,company
alice@example.com,Alice,Smith,Acme
bob@example.com,Bob,Jones,Corp
```

- `email` column required (case-insensitive)
- All other columns available as `{{column_name}}` merge fields in subject + body
- Row cap: 50,000

## Make targets

| Target | Description |
|---|---|
| `make install` | `uv sync` (Python deps) |
| `make gui` | Launch pywebview window |
| `make headless` | FastAPI only on `:8765` — browse at `http://127.0.0.1:8765` |
| `make test` | Run pytest |
| `make lint` | `ruff check` |
| `make format` | `ruff format` |
| `make clean` | Remove `__pycache__` and tool caches |

## Known limits

- **Encryption key** lives at `{user_data_dir}/key`. Losing it makes all stored SMTP passwords unrecoverable. Back it up.
- **Rate buckets** are in-memory — reset on app restart.
- **No retry backoff loop** — failed rows stay failed until you click Retry in the logs view.
- **Closing mid-campaign** aborts in-flight sends; queued rows stay in the DB and can be retried.
- **macOS Gatekeeper** will warn on first open if the binary isn't codesigned. Right-click → Open to bypass.
- **Attachments directory** (`{user_data_dir}/attachments`) grows unbounded — no cleanup in v1.

## Project layout

```
backend/
  alembic/          migrations
  app/
    routers/        HTTP endpoints (one file per resource)
    services/       business logic (smtp, crypto, mail-merge, etc.)
    models/         SQLAlchemy ORM
    schemas/        Pydantic v2 DTOs
    core/           logging, migrations
    utils/          errors, email validation
frontend/
  src/
    api/            axios clients + TypeScript types
    components/     UI primitives, TipTap editor, dropzone
    pages/          one file per route
    lib/            utils, formatters
```
