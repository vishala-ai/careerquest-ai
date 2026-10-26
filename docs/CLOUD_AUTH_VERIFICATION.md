# Cloud authentication verification — 2026-10-25

Status: implemented locally and packaged for a new Replit project. **Not published.** No cloud database or existing student history was transferred. No API keys were inspected or included in the archive.

Follow-up: [Replit import and hosted verification](REPLIT_IMPORT_VERIFICATION.md) supersedes the import blocker and native PostgreSQL limitations below. The original results remain here as the earlier checkpoint.

## Changes

- Self-registration using an alias username, passphrase and test-data acknowledgment. One account owns one Explorer; signup creates an account, and the existing setup form creates its Explorer. Neither action awards XP or confirms interests.
- Argon2id password hashes; opaque server-side sessions stored as hashes, 12-hour expiry, HttpOnly/SameSite=Strict cookies and Secure cookies for configured HTTPS origins. Session tokens/passwords are not stored in browser storage.
- Server-side ownership and CSRF checks for all profile APIs, legacy research/planning routes and saved PDFs. Existing unassigned profiles cannot be claimed through signup or a creation key. Public signup cannot choose another profile ID.
- Persisted login/registration limits, bounded hash concurrency, request-size limits including chunked bodies, sanitized validation errors, logout/revocation and host-only credential assignment/reset.
- Account identity replaces the browser-local Explorer registry in the authenticated app. Login resumes the account’s saved Explorer. Sign Out / Switch Account replaces public profile selection.
- Removed “fictional” from visible interface labels and the PDF footer. Kept concise alias/test-data notices. No raw quest responses, source catalogue, stored corrections or immutable portfolio history were rewritten.
- Added optional persistent PostgreSQL storage for Replit publishing; SQLite remains the local default. Cloud startup fails closed without a persistent database and configured HTTPS origin. Local-only developer tooling remains disabled in production.
- Source-only ZIP and Replit production launcher/setup documentation. No provider, model or agent contract changes.

The full [diff](test-evidence/cloud-auth.diff) and [changed-file list](test-evidence/cloud-auth-changed-files.json) include 56 source/config files. Existing backend regression files changed only their client fixture import; their behavioral assertions were preserved. The shared fixture uses real registered accounts/cookies. New negative security tests use the unwrapped FastAPI TestClient. One frontend assertion was updated for the requested replacement of “fictional information” with “aliases and test data.”

## Commands and final results

| Command | Actual result |
| --- | --- |
| `.venv/bin/python -m unittest discover -s tests -v` | **225 passed, 0 failed, 0 skipped**; includes 13 new authentication tests |
| `npm --prefix frontend test` | **194 passed, 0 failed, 0 skipped** |
| `npm --prefix frontend run build` | Passed; Vite 5.4.21, 1,632 modules |
| `.venv/bin/python -m compileall -q careerquest app.py tests scripts` | Passed |
| `PYTHONPATH=. .venv/bin/python scripts/smoke_core.py` | Passed: quests, XP, research, two roadmap versions, reflection and safe tool failure; 0 model calls |
| `CAREERQUEST_TEST_DATABASE_URL=postgresql://test@127.0.0.1:15438/test .venv/bin/python scripts/verify_postgres.py --pglite` | **225 run: 223 passed, 0 failed, 2 skipped** on an isolated local PGlite PostgreSQL protocol server |
| `.venv/bin/python scripts/package_replit.py` | Source-only ZIP generated; 158 allowlisted entries, no `.env`, database, virtual environment or node_modules |

Node commands used `/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin` on PATH. Dependencies were installed with `UV_CACHE_DIR=/private/tmp/careerquest-uv-cache uv pip install --python .venv/bin/python 'argon2-cffi>=23.1,<26' 'psycopg[binary]>=3.2,<4'`. Temporary PGlite packages were installed outside the repository for storage testing; they are not application dependencies.

Raw final logs: [backend](test-evidence/cloud-backend-tests.log), [frontend](test-evidence/cloud-frontend-tests.log), [PostgreSQL](test-evidence/cloud-postgres-tests.log), [build](test-evidence/cloud-build.log).

The PostgreSQL skips are the two parallel-creation tests: PGlite multiplexes one connection and cannot establish native PostgreSQL concurrency guarantees. Both parallel tests passed on SQLite. Run `scripts/verify_postgres.py` without `--pglite` against a dedicated native PostgreSQL test database before public release. All tests use isolated schemas/databases.

Earlier runs exposed fixture session revocation, PostgreSQL test-schema isolation, row/table metadata differences and timestamp precision. Fixes were verified in the final runs. In particular, SQLite REAL is mapped to PostgreSQL DOUBLE PRECISION so epoch timestamps do not round session expiration by roughly a minute. No failed behavioral assertion was removed to obtain a pass.

## Browser walkthrough and persistence

Used a separate database at `/private/tmp/careerquest-cloud-browser/alias-demo.sqlite3`, port 18116, with a test alias account. Verified:

1. Logged-out registration form; required acknowledgment and passphrase confirmation.
2. Account creation followed by existing avatar/nickname/grade setup, 0 XP and no profile confirmation.
3. “Start My First Quest” opens Quest 1 directly.
4. Save one quest, reload: correct nickname, Grade 11, one completed quest, 20 XP, “Continue Quest 2.”
5. Sign out, sign in: same Explorer and progress restored. No second Explorer was created.
6. Registration and returning Home at 375px; registration at 768px and 1280px. Document scroll width equaled viewport width. Registration body text measured 17px on mobile; heading measured 30px.
7. Keyboard Tab moved Username → Password → Confirm password; visible focus outline and associated accessible labels were inspected.

Screenshots: [registration desktop](test-evidence/cloud-register-desktop.png), [registration mobile](test-evidence/cloud-register-mobile.png), [returning mobile](test-evidence/cloud-returning-mobile.png). Captures precede the final label-size polish; the browser connection became unavailable before another capture. Reduced-motion CSS is present; changing the OS reduced-motion setting and testing with a screen-reader application were not performed.

The normal backend was restarted with:

```sh
.venv/bin/python -m uvicorn careerquest.api:app --host 127.0.0.1 --port 8000 --env-file .env --no-proxy-headers
```

Local database and environment were explicitly kept local, with cloud storage disabled for this process. `/api/health` returned 200 with authentication required and LangGraph enabled. Anonymous session returned `authenticated: false`; anonymous profile access returned 401. All existing business-table row counts and content hashes matched across restart. New auth tables are additive; no existing record was reset or assigned to a user automatically. Protected agent, LangGraph, Discovery, Research, profile-confirmation and milestone module hashes matched the pre-edit snapshot.

## Replit and remaining checks

The signed-in Replit account’s ZIP import screen was inspected. The source upload was blocked by the ChatGPT browser extension’s “Allow access to file URLs” setting; no Import submission or Publish action was performed. The browser connection later became unavailable. The user can upload [the verified ZIP](../exports/careerquest-replit.zip) using [the deployment instructions](CLOUD_DEPLOYMENT.md).

Unverified: actual Replit project import/build, managed production database connectivity, native PostgreSQL concurrency, HTTPS/proxy/cookie behavior on Replit, public login from separate devices, persistence across Replit redeployment, deployment costs and backup configuration. Existing local demo records are preserved locally and are not yet migrated. Groq generation was covered by existing mocked tests; no new live Groq inference was performed.
