# CareerQuest AI: new Replit project

This release adds self-registration and username/password login for an alias-only external demo. It is imported and verified in a Replit development preview, but has not been published. See [hosted verification](REPLIT_IMPORT_VERIFICATION.md). Use test data only; no real student names, contact information or records.

## Import and preview

1. Import `exports/careerquest-replit.zip` into a new Replit project. Keep source access private. If ZIP import is unavailable in your account, create a Python project, upload the ZIP and extract its contents into the project root. Do not ask Replit Agent to rebuild the application.
2. Select Run. `.replit` runs `bash scripts/replit-setup.sh` and `bash scripts/replit-run.sh`. Python 3.12+, Node 22, the existing React UI and FastAPI share port 8000.
   If Replit replaces the import’s run target with “Configure your app,” open Workflows, add a sequential Execute Shell Command task with that command, and make CareerQuest AI the default. The source configuration now includes this workflow. The installer explicitly sets `PIP_USER=false` so Replit’s user-install default does not conflict with the virtual environment.
3. In preview, the server reads Replit’s server-provided `REPLIT_DEV_DOMAIN` for its HTTPS origin. Alternatively set `CAREERQUEST_PUBLIC_ORIGIN` explicitly to the exact preview origin. Do not trust a browser-supplied host or forwarded header to configure it.
   Open that preview URL in its own browser tab for login. The app uses SameSite=Strict cookies; an embedded cross-site editor preview may block them. Do not weaken cookie protections to work around the embedded frame.
4. Add the existing `GROQ_API_KEY` through Replit’s server-side Secrets interface, never chat/source/React variables. Keep `GROQ_MODEL=openai/gpt-oss-120b`. Without the key, existing labeled bounded fallbacks remain available.
5. Register an alias and a passphrase of 15–128 characters. No email is collected. Create an Explorer, complete a quest, reload, sign out, sign in and confirm saved progress. Registration and Explorer creation award zero XP.

## Persistent cloud storage and publishing

Replit publishing uses a separate environment. Do not store published records in local SQLite. Provision Replit’s managed PostgreSQL database and confirm the production database is attached to the published app. See [Replit database guidance](https://docs.replit.com/build/add-database) and [publishing troubleshooting](https://docs.replit.com/build/troubleshooting).

Set these in **production** settings, not just the editor:

| Setting | Value |
| --- | --- |
| `DATABASE_URL` | Managed PostgreSQL connection supplied by Replit; keep private |
| `CAREERQUEST_PUBLIC_ORIGIN` | Exact `https://your-project.replit.app` origin, no path; use the selected domain |
| `GROQ_API_KEY` | Existing server-side Groq credential, if live generation is desired |
| `GROQ_MODEL` | `openai/gpt-oss-120b` |
| `CAREERQUEST_DATABASE_SCHEMA` | `careerquest_demo` for this Replit project; creates a separate app namespace without resetting other schemas |

Production build: `bash scripts/replit-setup.sh`.

Production run: `bash scripts/replit-production.sh`.

The production launcher forces `CAREERQUEST_ENV=production`, `CAREERQUEST_DEV_TOOLS=0` and `CAREERQUEST_HOST=0.0.0.0`. Startup fails without persistent PostgreSQL and a valid HTTPS origin. Secure, HttpOnly, SameSite=Strict cookies are enabled for HTTPS. Uvicorn does not trust arbitrary forwarded headers. Use a TLS-verified PostgreSQL connection as supplied by the provider; never disable certificate verification to make a failed connection work.

Review Replit’s displayed hosting/database costs before publishing. This package does not purchase a plan or publish an application. After publishing, repeat login/quest/reload checks on the public URL, restart/redeploy and verify records still exist. Check database backups in the provider before inviting a group.

## Account boundaries and existing records

- Each account owns at most one Explorer. A username and account-bound creation transaction prevent duplicate Explorers after retries; browser-local IDs are no longer authority.
- Every profile API, saved PDF and legacy research/roadmap route checks server-side ownership. Another account’s IDs return 404. A global profile directory is not exposed.
- Existing local records stay on this computer and are excluded from the import ZIP. They are not deleted, automatically claimed or migrated. A fresh Replit database starts empty. Transferring existing histories is a separate, explicit migration; copying a SQLite file into a published filesystem is not a durable migration.
- To give an existing **local demo profile** a login, run the host-only CLI below. It prompts privately for a passphrase and refuses an already owned profile. It changes only account ownership, not profile history, confirmations or XP.

```sh
.venv/bin/python scripts/account_admin.py assign --username demo_alias --profile-id PROFILE_UUID
.venv/bin/python scripts/account_admin.py reset --username demo_alias
```

On Replit, use `.venv-replit/bin/python` instead. Password reset revokes that account’s sessions. There is no public reset endpoint or email recovery; the demo host must perform resets. Never put passwords in shell arguments. Old unassigned records cannot be claimed by a public signup.

Session duration is 12 hours. Auth attempts are rate-limited in the database: 10 registrations per observed peer and 100 overall per hour; 10 login attempts per username and 60 per observed peer per 15 minutes. Forwarded IP headers are not trusted. A reverse proxy may share the peer budget across visitors; plan a group demo accordingly. Password hashing concurrency is bounded to two operations per application process.

## Storage adapter and verification

Local SQLite and Streamlit code remain available. `DATABASE_URL` selects the PostgreSQL adapter for the same tables and SQL operations. An appended database-generated row ID preserves insertion order; PostgreSQL advisory transaction locks preserve the existing serialized write/version-allocation behavior. Existing domain APIs, source validation, confirmation gates and immutable portfolio snapshots are retained. Do not publish the unauthenticated Streamlit fallback.

```sh
python -m unittest discover -s tests -v
python -m compileall -q careerquest app.py tests scripts
npm --prefix frontend test
npm --prefix frontend run build
python scripts/package_replit.py
```

In the Replit shell, run SQLite regression tests with the hosted settings cleared **for the test process only**:

```sh
REPLIT_DEV_DOMAIN= REPLIT_DEPLOYMENT=0 CAREERQUEST_PUBLIC_ORIGIN= CAREERQUEST_ENV=local CAREERQUEST_HOST=127.0.0.1 DATABASE_URL= .venv-replit/bin/python -m unittest discover -s tests -v
```

Explicit SQLite paths now stay local even when a cloud URL is inherited. The FastAPI adapter and host CLI explicitly select the configured cloud URL. Still clear hosted settings for the ordinary SQLite fixture suite: unpatched API defaults and host checks must not use the application’s cloud settings. For PostgreSQL, use the isolated-schema runner below. Never clear or reset an application database to make tests pass.

For **a separate native PostgreSQL test database**, configure `CAREERQUEST_TEST_DATABASE_URL` privately and run:

```sh
python scripts/verify_postgres.py
```

The runner creates isolated randomly named `cq_test_*` schemas, runs the same backend assertions and removes only those schemas. Do not point test tooling at the production database. `--pglite` skips two concurrency checks because PGlite multiplexes one connection; it is a local SQL compatibility check, not a substitute for native PostgreSQL concurrency verification. Live Replit storage, proxy/cookie behavior, production scaling and native PostgreSQL concurrency still require checks in the new project.

Model routing and generation tests use mocks; cloud authentication work does not constitute a new live Groq smoke test. UI wording uses “demo,” “Explorer” and “test data.” Raw history and curated source content are not rewritten to remove historical wording.
