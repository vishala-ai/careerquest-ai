# Replit import and hosted verification — 2026-10-25

Project created: [CareerQuest AI](https://replit.com/@vishalak-AI/CareerQuest-AI).

Development preview: [Open CareerQuest AI](https://8034bb00-7561-4364-af84-c5087b51a72c-00-27oipj5cxt3wu.kirk.replit.dev/).

This is an editor development preview, **not a published production deployment**. No Publish action, paid plan upgrade or hosting purchase was accepted. No local database or `.env` was uploaded. The original source ZIP’s SHA-256 was `fa25d0a07880c2b43785a0f33c63932fb4002e522994829a855d513b7f4ad92e` (158 allowlisted source entries). Subsequent integration fixes were applied to both local and Replit sources.

## Verified hosted results

| Check | Actual result |
| --- | --- |
| Python dependency installation | Passed after overriding Replit’s user-install default with `PIP_USER=false` |
| React production build | Passed on Replit: Vite 5.4.21, 1,632 modules |
| Backend suite on isolated SQLite fixtures | **226 passed, 0 failed, 0 skipped**; 39.268 seconds on Replit |
| Same suite on native PostgreSQL in isolated schemas | **226 passed, 0 failed, 0 skipped**; 261.570 seconds; includes concurrency and fresh-process persistence |
| Frontend tests on Replit | **194 passed, 0 failed, 0 skipped** |
| Python compilation on Replit | Passed |
| Local backend suite after integration fixes | **226 passed, 0 failed, 0 skipped** |

Hosted backend command:

```sh
REPLIT_DEV_DOMAIN= REPLIT_DEPLOYMENT=0 CAREERQUEST_PUBLIC_ORIGIN= CAREERQUEST_ENV=local CAREERQUEST_HOST=127.0.0.1 DATABASE_URL= .venv-replit/bin/python -m unittest discover -s tests -v
```

Hosted native PostgreSQL command (the connection is passed internally, never displayed):

```sh
CAREERQUEST_TEST_DATABASE_URL="$DATABASE_URL" DATABASE_URL= REPLIT_DEV_DOMAIN= REPLIT_DEPLOYMENT=0 CAREERQUEST_PUBLIC_ORIGIN= CAREERQUEST_ENV=local CAREERQUEST_HOST=127.0.0.1 .venv-replit/bin/python scripts/verify_postgres.py
```

The PostgreSQL runner creates and removes only its random `cq_test_*` schemas. It does not reset application records. The two former PGlite concurrency skips were exercised successfully on native PostgreSQL.

```sh
npm --prefix frontend test
.venv-replit/bin/python -m compileall -q careerquest app.py tests scripts
```

Hosted logs remain at `/tmp/careerquest-replit-tests-final.log`, `/tmp/careerquest-replit-native-postgres.log` and `/tmp/careerquest-replit-frontend-tests.log` in the Replit workspace. [Hosted test screenshot](test-evidence/replit-native-tests.png).

## Browser walkthrough

Used a test-only alias account and “Orbit Cloud Demo,” Grade 11. No real student information was entered.

- Registration succeeded over the separate HTTPS preview tab; Explorer setup showed zero XP.
- Creating one Explorer opened “Welcome aboard” and the direct Quest 1 action.
- Saving Quest 1 awarded 20 XP and opened Quest 2.
- Reload restored the same Explorer, one completed quest, 20 XP and “Continue Quest 2.”
- Sign out returned to login; sign in restored the same progress.
- Stop/Run of the Replit workflow followed by browser reload retained the session, Explorer and 20 XP. An aggregate check confirmed exactly one account and one Explorer in the demo namespace, with the earlier default-namespace fixture counts unchanged.
- Personalized research remained locked pending quests and explicit profile confirmation.

[Hosted Home screenshot](test-evidence/replit-preview-home.png). This was a development-preview smoke test, not a full live Groq/portfolio walkthrough.

## Reproduced issues and fixes

1. **Run workflow:** Replit initially substituted a “Configure your app” placeholder. Created the sequential CareerQuest AI workflow using the existing setup/run scripts and made it the default. Added the workflow definition to local `.replit` for future imports.
2. **pip environment:** Initial install failed because Replit’s user-install setting conflicts with a virtual environment. The installer now runs pip with `PIP_USER=false`. No dependency versions or model providers were changed.
3. **Hosted test isolation:** The first backend run inherited the preview hostname and cloud database. It failed with 207 failures and 3 errors; some synthetic fixture records were added to the default database namespace, and the signup rate limit was reached. The next run cleared the host/database settings but retained the shared bind address, producing 3 failures and 4 errors at local-only developer gates. The final run used explicit local test settings and passed all assertions.
4. **Storage target boundary:** An inherited database URL previously overrode even explicit temporary SQLite paths. `store.connect(path)` now honors explicit SQLite paths; only a PostgreSQL URL selects the cloud adapter. FastAPI and the host CLI explicitly choose the configured cloud URL. A fresh-process regression test proves an explicit SQLite path never connects to an inherited cloud URL.
5. **Demo/test separation:** Added `CAREERQUEST_DATABASE_SCHEMA=careerquest_demo`, validated and created under the existing PostgreSQL write lock. Application data uses that namespace; native tests use unique temporary namespaces. The earlier default-namespace fixture records were preserved, not deleted or reset. The initial aggregate check found 10 test accounts and 29 profiles there. Database namespace `public` does not mean those records are exposed on the website; API ownership gates still apply.

Changed source/config files for these fixes: `.replit`, `scripts/replit-setup.sh`, `careerquest/store.py`, `careerquest/postgres.py`, `careerquest/api.py`, `scripts/account_admin.py`, `tests/test_auth.py`. Documentation and the import package were updated too. No agent, model, catalogue, XP reward or profile-confirmation contract was rewritten. Local business-table hashes still matched the pre-authentication baseline after this work.

## Remaining release work

- Production publishing and its selected HTTPS origin.
- Confirm the **production** PostgreSQL connection and schema settings in Replit’s publishing environment; the verified database here is the development database.
- Configure the existing Groq credential privately in server-side Secrets if live AI is wanted. No secret value was inspected, copied or entered, and no live Groq smoke test was performed.
- Verify persistence after a published redeployment, production backups and access from a separate external browser/device.
- Existing local demo profiles and portfolios remain local; they have not been migrated or publicly claimed.

No behavioral assertion was weakened to obtain a pass. The only new backend assertion checks the explicit SQLite/cloud storage boundary.
