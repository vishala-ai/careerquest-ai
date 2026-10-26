# CareerQuest React + FastAPI: local and Replit setup

Replit preparation preserves the existing app. It does not finish the remaining
UI specification pages or add authenticated student accounts. See
[increment one](SPEC_INCREMENT_1.md) and [the Replit handoff](../replit.md).

## Import into Replit

1. Generate the source-only package locally:
   `.venv/bin/python scripts/package_replit.py`.
2. Open [Replit Import](https://replit.com/import), select ZIP, and upload
   `exports/careerquest-replit.zip`. See the official
   [import guide](https://docs.replit.com/build/import-from-providers).
3. Configure restricted preview access before running. The demo has no
   authentication. Use fictional data only; do not publish it for real students.
4. In backend [Secrets](https://docs.replit.com/core-concepts/project-editor/app-setup/secrets),
   enter `GROQ_API_KEY` yourself. `GROQ_MODEL=openai/gpt-oss-120b` is already in
   `.replit`. Do not upload your local `.env` or use a `VITE_` credential.
   No key is needed for the default deterministic routing mode.
5. Select Run. `.replit` requests Python 3.12 and Node.js 22, installs Python
   packages into `.venv-replit`, runs `npm ci`, builds React, then starts FastAPI
   on port 8000. FastAPI serves both the UI and `/api`; no two-server proxy is
   needed. Runtime module availability must still be verified in Replit.
6. Open `/api/health` in preview. Expect `status: ok` and
   `agent_engine: langgraph`. Then follow the verification commands in `replit.md`.

Configuration follows Replit's [run/port configuration](https://docs.replit.com/features/project-setup/configuration).
These files have been prepared locally. An actual Replit import, package
installation and hosted preview must be checked there before claiming success.

## Data and model behavior

The ZIP uses an explicit source-file allowlist. It contains source, tests,
synthetic catalog/demo fixture, lockfile and specification references. It excludes
local `.env`, SQLite databases, `var/`, browser selections, installed dependencies,
build output and test screenshots. The original local database is untouched.
The imported workspace starts without those local explorer records and creates
its own SQLite database at `var/careerquest-react.sqlite3` when used. Existing
records in a Replit workspace are not deleted by either startup script.

`CAREERQUEST_DB` may select a different SQLite path. No hosted persistence or
production database migration is configured. Workspace SQLite should not be
assumed to persist across publishing/redeployment. A separate reviewed migration
would be needed to transfer existing synthetic records.

Optional Groq routing selects one allowed action and falls back to bounded
deterministic routing on errors. It does not provide live research: citations
come from the curated offline catalog. LangGraph and Streamlit remain intact.
No external write or deployment is performed by these preparation scripts.

## Local development

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-api.txt httpx
.venv/bin/python -m uvicorn careerquest.api:app --host 127.0.0.1 --port 8000
```

For a separate Vite development server:

```sh
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` to localhost:8000.
Alternatively, build with `npm --prefix frontend run build`, then restart the
backend and open http://127.0.0.1:8000 for the single-port app.

The project-root `.env` is loaded by the backend; existing process environment
variables take precedence. Restart after configuration changes. The Streamlit
fallback remains available with `.venv/bin/python -m streamlit run app.py
--server.address 127.0.0.1` and keeps its existing separate database behavior.
