# Email-Sending Desktop App — Implementation Plan

## Context

User wants a self-hosted, UI-driven email **desktop application** that can compose and send single emails plus run bulk send jobs (e.g. 100 personalised emails to 100 recipients with one button). It wraps SMTP plumbing in a usable interface and provides the standard utilities that turn raw SMTP into a workable mass-mail tool — templates, contacts, rate-limiting, send logs, attachments.

The project directory (`/Users/rohitagarwal/learning-projects/misc/email-app/`) is a fresh `uv`-style Python 3.13 project with no code yet (`main.py` is a stub, `pyproject.toml` has zero dependencies). Everything is greenfield.

**Locked design decisions:**
- Shell: **PyWebView** desktop window (system webview — WKWebView on macOS, WebView2 on Windows, WebKitGTK on Linux). Single process.
- Backend: **FastAPI** running in-thread inside the same Python process (uvicorn programmatic start). Bound to random free port on `127.0.0.1`.
- Frontend: **React + Vite + TypeScript**. Production build (`dist/`) served as static files by FastAPI. Dev mode points pywebview at Vite dev server.
- SMTP source: **user-supplied SMTP creds** (Fernet-encrypted at rest)
- Auth: **none** — same-process same-origin, no network exposure
- Database: **SQLite** (aiosqlite + SQLAlchemy async + Alembic). File lives in OS user-data dir.
- Editor: **Rich text HTML** (TipTap) with auto-derived plain-text fallback (multipart/alternative)
- Queue: **FastAPI BackgroundTasks** only (no Celery, no scheduled send — dropped)
- Bulk features: CSV mail-merge, per-minute rate limiting, send logs with retry, templates library, contacts/groups, attachments
- Packaging: **PyInstaller** → `.app` (macOS), `.exe` (Windows), AppImage/binary (Linux). Frontend `dist/` bundled as data files.

---

## 1. Repository Layout

```
/Users/rohitagarwal/learning-projects/misc/email-app/
├── .python-version                  # already present (3.13)
├── .gitignore                       # extend with .venv/, dist/, build/, node_modules/, *.spec
├── README.md                        # quickstart + build instructions
├── pyproject.toml                   # rewritten with deps (see §8)
├── uv.lock
├── .env.example                     # dev only
├── Makefile                         # dev, build-frontend, package targets
├── app.spec                         # PyInstaller spec (generated, then committed)
│
├── backend/
│   ├── alembic.ini
│   ├── alembic/{env.py, script.py.mako, versions/}
│   ├── app/
│   │   ├── __main__.py             # `python -m app` entrypoint: start FastAPI thread + open pywebview window
│   │   ├── desktop.py              # pywebview bootstrap, port picker, lifecycle
│   │   ├── server.py               # uvicorn.Config + Server, programmatic run
│   │   ├── main.py                 # FastAPI app, router mount, static mount, lifespan
│   │   ├── config.py               # pydantic-settings Settings, platformdirs paths
│   │   ├── paths.py                # resolve user_data_dir / bundled resources dir (PyInstaller-aware)
│   │   ├── db.py                   # async engine + session factory + Base (SQLite)
│   │   ├── deps.py                 # get_db, get_settings
│   │   ├── models/                 # base, smtp_account, contact, template, campaign, attachment
│   │   ├── schemas/                # pydantic v2 DTOs per resource
│   │   ├── routers/                # smtp_accounts, contacts, groups, templates, campaigns, send, attachments, health
│   │   ├── services/               # crypto, smtp_sender, mail_merge, csv_parser, html_sanitizer, text_fallback, rate_limiter, attachment_store, campaign_runner
│   │   └── utils/                  # email_validate, errors
│   └── tests/
│
└── frontend/
    ├── package.json, vite.config.ts, tsconfig.json, tailwind.config.ts, components.json
    └── src/
        ├── main.tsx, App.tsx
        ├── api/                    # client.ts (axios baseURL via window.__API_BASE__ injected by pywebview), per-resource modules, types.ts
        ├── hooks/                  # TanStack Query hooks per resource + useCampaignProgress
        ├── components/
        │   ├── layout/{Sidebar, TopBar}
        │   ├── editor/{RichTextEditor (TipTap), EditorToolbar, PlaceholderHelper}
        │   ├── RecipientPicker, AttachmentDropzone, ProgressBar, CsvUploader, CsvPreviewTable, MergePreviewDialog, ConfirmDialog
        │   └── ui/                 # shadcn primitives
        ├── pages/                  # Dashboard, Compose, BulkSend, Templates, TemplateEdit, Contacts, ContactEdit, Groups, SmtpSettings, Logs, CampaignDetail
        ├── lib/                    # utils, formatDate, constants
        └── styles/globals.css
```

`frontend/dist/` (built) is bundled into the PyInstaller binary; backend serves it at `/`.

---

## 2. Desktop Bootstrap

### `backend/app/__main__.py`
```python
def main() -> None:
    from app.desktop import launch
    launch()
```

### `backend/app/desktop.py`
```python
import socket, threading, webview
from app.server import run_server
from app.config import get_settings

def pick_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def launch() -> None:
    settings = get_settings()
    port = pick_free_port()
    ready = threading.Event()
    t = threading.Thread(target=run_server, args=(port, ready), daemon=True)
    t.start()
    ready.wait(timeout=10)
    url = f"http://127.0.0.1:{port}/"
    window = webview.create_window(
        title="Email App",
        url=url,
        width=1280, height=860,
        min_size=(960, 640),
        confirm_close=True,
    )
    webview.start()  # blocking; returns on window close
```

### `backend/app/server.py`
```python
import asyncio, uvicorn, threading
from app.main import app

def run_server(port: int, ready: threading.Event) -> None:
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", loop="asyncio")
    server = uvicorn.Server(config)

    async def serve() -> None:
        task = asyncio.create_task(server.serve())
        while not server.started:
            await asyncio.sleep(0.05)
        ready.set()
        await task

    asyncio.run(serve())
```

Dev mode override: if `EMAIL_APP_DEV=1`, `desktop.launch` skips serving frontend statically and opens `http://localhost:5173` (Vite dev server, run separately). FastAPI still on random port; API client reads it from `window.__API_BASE__` injected via `webview.create_window(js_api=…)` or fetched from `/__config`.

---

## 3. Backend — Modules & Responsibilities

### Paths (`backend/app/paths.py`)
- `is_frozen()` → `getattr(sys, "frozen", False)` (PyInstaller).
- `resource_dir()` → `Path(sys._MEIPASS)` if frozen else repo root. Used to locate bundled `frontend/dist/`, alembic migrations.
- `user_data_dir()` → `platformdirs.user_data_dir("EmailApp", "rohit")`. Houses `app.db` (SQLite), `key` (Fernet), `attachments/`, `logs/`.
- All dirs created `0o700` on first launch.

### Config (`backend/app/config.py`)
`Settings(BaseSettings)`:
- `DATABASE_URL` default `sqlite+aiosqlite:///{user_data_dir}/app.db`
- `KEY_FILE` default `{user_data_dir}/key`
- `ATTACHMENT_DIR` default `{user_data_dir}/attachments`
- `MAX_ATTACHMENT_MB = 25`
- `BIND_HOST = "127.0.0.1"`
- `ALLOWED_ATTACHMENT_MIMES` (explicit allowlist)
- `DEV_MODE` from `EMAIL_APP_DEV`

`@lru_cache` factory `get_settings()`.

### DB (`backend/app/db.py`)
- `async_engine = create_async_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})`
- SQLite pragmas on connect: `PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA synchronous=NORMAL;` (via `event.listens_for(engine.sync_engine, "connect")`).
- `AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)`
- `class Base(DeclarativeBase)`
- `get_db()` async generator FastAPI dependency.

### Models (`backend/app/models/`)
- **base.py** — `Base(DeclarativeBase)`, `TimestampMixin` (`created_at`, `updated_at` server defaults via `func.now()`).
- **smtp_account.py** — `SmtpAccount`: id UUID PK (stored as TEXT), name, host, port, username, `password_encrypted` BLOB, `use_tls` (STARTTLS), `use_ssl` (implicit), from_email, from_name, `max_per_minute` (default 30), `max_per_hour` (default 500), `is_default`.
- **contact.py** — `Contact` (email unique, first/last name, `extra_json` TEXT containing JSON for free-form merge fields), `ContactGroup`, `Tag`, M2M association tables.
- **template.py** — `Template`: name unique, subject, `body_html`, `body_text` (nullable, auto-derived if null), nullable FK to SmtpAccount.
- **campaign.py** —
  - `Campaign`: name, subject, body_html, smtp_account_id FK, template_id FK nullable, `status` Enum(queued/running/done/failed/cancelled), total, sent_count, failed_count, started_at, finished_at.
  - `EmailLog`: campaign_id FK nullable, to_email, `merge_data` TEXT(JSON), `subject_rendered`, `body_html_rendered`, `status` Enum(queued/sending/sent/failed/retrying), error_message, attempts, sent_at.
  - Indexes: `(campaign_id, status)`, `(status, created_at)`.
- **attachment.py** — `Attachment`: filename, stored_name (UUID on disk), mime_type, size_bytes, nullable FKs (campaign_id, email_log_id, template_id). M2M pivot `email_log_attachments`.

UUIDs stored as TEXT (SQLite has no native UUID).

### Routers (`backend/app/routers/`, mounted under `/api`)

Same as web plan, unchanged endpoints:
- `smtp_accounts` (CRUD + `/test`), `contacts`, `groups`, `templates` (+ `/preview`), `campaigns` (+ `/from-csv`, `/cancel`, `/logs/{id}/retry`), `send`, `attachments`, `health`.

### Static frontend serving (in `main.py`)
```python
from fastapi.staticfiles import StaticFiles
from app.paths import resource_dir, is_frozen

if not get_settings().DEV_MODE:
    dist = resource_dir() / "frontend" / "dist"
    app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
```
SPA fallback: custom 404 handler returns `index.html` for non-`/api` paths.

### Services (`backend/app/services/`)

Same as web plan. Notes:
- **crypto.py** — Fernet. Key path = `settings.KEY_FILE` (under user data dir). Auto-generated `0o600` on first launch.
- **smtp_sender.py** — unchanged (aiosmtplib).
- **mail_merge.py** — unchanged (Jinja2 `SandboxedEnvironment`).
- **csv_parser.py** — unchanged.
- **html_sanitizer.py** — unchanged (bleach allowlist).
- **text_fallback.py** — unchanged (html2text).
- **rate_limiter.py** — unchanged (in-memory token bucket, single-process safe).
- **attachment_store.py** — saves under `settings.ATTACHMENT_DIR` (user data dir).
- **campaign_runner.py** — unchanged (BackgroundTasks worker with fresh AsyncSession).

### Schemas
Pydantic v2 per resource — unchanged.

### App entrypoint (`backend/app/main.py`)
- No CORS middleware (same-origin).
- `lifespan` warms Fernet key, ensures user data dirs, runs `alembic upgrade head` programmatically on startup if `DATABASE_URL` is SQLite, disposes engine on shutdown.
- Custom exception handlers for `SmtpSendError`, `ValidationError`.

---

## 4. Frontend — Pages & Components

Routing, pages, components: identical to web plan (Dashboard, Compose, BulkSend, Templates, Contacts, Groups, SmtpSettings, Logs, CampaignDetail).

### API client (`frontend/src/api/client.ts`)
```ts
// In bundled mode, dist is served by FastAPI on same origin → relative URLs.
// In dev mode, Vite proxies /api to the backend port (read from /__config endpoint at boot).
const base = import.meta.env.DEV ? await fetch("/__config").then(r => r.json()).then(c => c.apiBase) : "";
export const api = axios.create({ baseURL: `${base}/api` });
```
Vite dev proxy in `vite.config.ts`:
```ts
server: { proxy: { "/api": { target: process.env.VITE_API_TARGET, changeOrigin: true } } }
```
`VITE_API_TARGET` set by `make dev` to the random backend port (or use a fixed dev port `8765`).

### Build output
`vite build` → `frontend/dist/`. Hashed asset filenames. Committed-ignored.

State (TanStack Query), styling (Tailwind + shadcn), key components — unchanged from web plan.

---

## 5. Bulk Send Flow

Unchanged from web plan (§4 of prior version). The wire format and UX are identical because the desktop shell is a thin window around the same React app + FastAPI.

---

## 6. CSV Mail-Merge Format

Unchanged.

---

## 7. Rate Limiting

Unchanged. In-memory buckets are safe because the desktop app runs a single uvicorn worker by construction.

---

## 8. Security

1. **SMTP passwords**: Fernet-encrypted at rest. Key at `{user_data_dir}/key` (`0o600`, parent `0o700`). Never returned in any API response.
2. **Network**: uvicorn binds `127.0.0.1` on a random ephemeral port. Same-origin: the webview hits the same port that serves the SPA. No external network exposure by construction.
3. **No CORS, no auth**: same process, same origin, single user. Document that any other local process on the machine *could* reach the API on that port — acceptable tradeoff for v1.
4. **HTML sanitization**: every body passes `bleach.clean` allowlist *after* Jinja render, *before* SMTP send.
5. **Attachments**: size cap (25 MB default), MIME allowlist via `python-magic`, UUID-named on disk, original filename only used for `Content-Disposition`.
6. **Email validation**: `email-validator` with `check_deliverability=False`.
7. **CSV upload**: streamed parse with row cap 50_000.
8. **SQLite file**: lives under user data dir with `0o700` parent. WAL mode for crash safety.

---

## 9. Dependencies

### Backend `pyproject.toml`
```toml
[project]
name = "email-app"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.32",
  "sqlalchemy[asyncio]>=2.0.36",
  "aiosqlite>=0.20",
  "alembic>=1.14",
  "pydantic>=2.9",
  "pydantic-settings>=2.6",
  "aiosmtplib>=3.0",
  "jinja2>=3.1",
  "cryptography>=43",
  "bleach>=6.2",
  "html2text>=2024.2.26",
  "python-multipart>=0.0.17",
  "email-validator>=2.2",
  "python-magic>=0.4.27",
  "platformdirs>=4.3",
  "pywebview>=5.3",
]

[dependency-groups]
dev = [
  "pytest>=8.3",
  "pytest-asyncio>=0.24",
  "httpx>=0.27",
  "aiosmtpd>=1.4",
  "ruff>=0.7",
  "mypy>=1.13",
  "pyinstaller>=6.11",
]

[project.scripts]
email-app = "app.__main__:main"

[tool.pytest.ini_options]
asyncio_mode = "auto"
```
Install: `uv sync`.

### Frontend (`frontend/package.json`)
Unchanged from web plan (React, TanStack Query, TipTap, axios, papaparse, react-dropzone, shadcn-ui, etc.).

---

## 10. Packaging — PyInstaller

### Build steps
1. `cd frontend && npm ci && npm run build` → produces `frontend/dist/`.
2. `uv run pyinstaller app.spec` → produces `dist/EmailApp.app` (macOS) / `dist/EmailApp.exe` (Windows) / `dist/EmailApp` (Linux).

### `app.spec` (key parts)
```python
# pyinstaller --name EmailApp --windowed --add-data "frontend/dist:frontend/dist" --add-data "backend/alembic:alembic" backend/app/__main__.py
a = Analysis(
    ['backend/app/__main__.py'],
    pathex=['backend'],
    datas=[
        ('frontend/dist', 'frontend/dist'),
        ('backend/alembic', 'alembic'),
        ('backend/alembic.ini', '.'),
    ],
    hiddenimports=['aiosqlite', 'app.models', 'app.routers', 'app.services'],
    ...
)
# macOS: build .app bundle via BUNDLE(); set CFBundleIdentifier="com.rohit.emailapp"
# Windows: --windowed (no console)
# Linux: --onefile for single AppImage-style binary
```

### Platform notes
- **macOS**: needs codesigning + notarization for distribution outside dev machine (`codesign --deep --options runtime --sign "Developer ID Application: …"`, then `xcrun notarytool submit`). v1 dev-machine-only — skip.
- **Windows**: WebView2 runtime must be installed (Win11 has it; Win10 may need installer redistributable). PyWebView documents this.
- **Linux**: WebKitGTK runtime required (`libwebkit2gtk-4.1`). Document in README.
- **python-magic**: needs `libmagic` bundled. On macOS use `python-magic-bin` or install `libmagic` via brew and bundle dylib via `--add-binary`. Document.

---

## 11. Critical Files to Implement

- `backend/app/__main__.py`, `desktop.py`, `server.py`
- `backend/app/main.py`
- `backend/app/config.py`, `paths.py`
- `backend/app/db.py` (SQLite pragmas)
- `backend/app/models/{smtp_account,contact,template,campaign,attachment}.py`
- `backend/app/services/crypto.py`
- `backend/app/services/smtp_sender.py`
- `backend/app/services/mail_merge.py`
- `backend/app/services/rate_limiter.py`
- `backend/app/services/campaign_runner.py`   ← core of bulk send
- `backend/app/routers/campaigns.py`           ← orchestrates bulk
- `backend/alembic/env.py` + initial migration
- `frontend/src/App.tsx` + routing
- `frontend/src/pages/BulkSendPage.tsx`        ← headline UX
- `frontend/src/pages/CampaignDetailPage.tsx`  ← live progress
- `frontend/src/components/editor/RichTextEditor.tsx`
- `frontend/src/hooks/useCampaignProgress.ts`
- `frontend/src/api/client.ts`                 ← reads runtime API base
- `app.spec` (PyInstaller)
- `pyproject.toml`, `Makefile`, `.env.example`, `README.md`

---

## 12. Verification (End-to-End Test)

### Dev mode
1. `uv sync`
2. `cd frontend && npm install && npm run dev` → Vite on `http://localhost:5173`.
3. Separate shell: `docker run -p 1025:1025 -p 8025:8025 axllent/mailpit` (dev SMTP).
4. `EMAIL_APP_DEV=1 VITE_API_TARGET=http://127.0.0.1:8765 uv run python -m app` → pywebview window opens on Vite URL, FastAPI on 8765.

### Packaged mode
1. `make build-frontend` → `frontend/dist/`
2. `make package` → `dist/EmailApp.app` (or `.exe`/binary).
3. Double-click `EmailApp.app`. First launch creates user data dir + key + SQLite db + runs migrations.
4. **SMTP**: `/smtp` → host=`localhost`, port=`1025` (Mailpit), TLS off, from=`me@test.local`. Click **Test** → Mailpit (`http://localhost:8025`) shows message.
5. Add 3 contacts.
6. Create template `Welcome`, subject `Hi {{first_name}}`, body `<p>Hi {{first_name}}, welcome to Acme.</p>`.
7. CSV with `email,first_name` × 3 rows.
8. `/bulk` → SMTP=Mailpit → template=Welcome → upload CSV → preview row 1 → Send.
9. Watch `/campaigns/:id` — ProgressBar 0→3.
10. Mailpit shows 3 personalised messages.
11. **Negative**: stop Mailpit, send again → failed rows. Restart Mailpit, click Retry → succeeds.
12. **Attachment**: compose with 1 MB PDF → Mailpit shows attachment.
13. **Rate limit**: `max_per_minute=6`, 12-row CSV → total time >1 minute.
14. **Crash recovery**: kill app mid-campaign, relaunch → queued rows still in DB (visible in `/logs`). Retry per-row.

---

## 13. Known Limits / Things the User Must Accept

1. **Gmail** needs an App Password. Host `smtp.gmail.com`, port `587`, STARTTLS.
2. **Deliverability**: residential IP without SPF/DKIM/DMARC = spam. Point SMTP settings at SES/Postmark/Resend for real volume.
3. **Rate limiter is courtesy**, not a hard guarantee.
4. **No code signing in v1**: macOS Gatekeeper will warn; user must right-click → Open the first time. Windows SmartScreen similar.
5. **WebView2 (Windows)** and **WebKitGTK (Linux)** are OS-level deps. Bundled installer would solve this but is out of scope.
6. **Encryption key irreplaceable**: lose `{user_data_dir}/key` → all stored SMTP passwords become garbage. Back it up.
7. **In-memory rate buckets** reset on app restart.
8. **No scheduled send and no retry-with-backoff loop**: failed rows stay failed until user clicks Retry.
9. **Background task lifecycle**: closing the window mid-campaign aborts in-flight sends; queued rows remain queued in DB. Retry from `/logs`.
10. **Outlook HTML quirks**: TipTap output is sanitized; some niche CSS stripped.
11. **Attachment dir grows unbounded** under `{user_data_dir}/attachments`. No cleanup job in v1.
12. **CSV row cap 50_000** (memory safety).
13. **SQLite** is single-writer; concurrent campaigns serialize at the write layer. Fine for desktop, would not scale to multi-user.
14. **python-magic / libmagic**: bundling libmagic into PyInstaller is platform-fiddly. Fallback to declared MIME if `magic` unavailable.
