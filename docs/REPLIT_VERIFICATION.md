# Replit preparation verification

Prepared the existing React + FastAPI app for import. No application business
logic, schema, local explorer records, LangGraph workflow, Streamlit fallback or
test expectations changed. No upload, Replit app creation or deployment occurred.
The Replit integration was available but not installed/connected in this session.

Files added: `.replit`, `replit.md`, `scripts/replit-setup.sh`,
`scripts/replit-run.sh`, `scripts/package_replit.py`,
`tests/test_replit_package.py`, and this report.
Files updated: `.gitignore`, `README.md`, `docs/REACT_REPLIT_SETUP.md`.
Generated artifact: `exports/careerquest-replit.zip` (ignored by source control).

Commands executed from the project root:

```sh
.venv/bin/python -m unittest discover -s tests -v
bash -n scripts/replit-setup.sh scripts/replit-run.sh
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-baseline-pycache .venv/bin/python -m compileall -q careerquest app.py tests scripts
PYTHONPATH=. .venv/bin/python scripts/smoke_core.py
.venv/bin/python scripts/package_replit.py
```

From `frontend/`:

```sh
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm run build
```

Results: **33 Python tests and 7 frontend tests passed; zero failures or test
skips.** Two added tests verify that credential/runtime fixtures are omitted
from the package and linked source files are rejected. Backend compilation,
shell syntax, offline core smoke and React production build passed.

Additional inline Python checks parsed `.replit` with `tomllib`, verified ZIP
integrity/required files/exclusions, and launched `bash scripts/replit-run.sh`
using the existing absolute `.venv/bin/python` path through
`CAREERQUEST_PYTHON`, `CAREERQUEST_HOST=127.0.0.1`, `PORT=18081`, and a temporary
`CAREERQUEST_DB`. `/api/health` returned `status: ok` with LangGraph, and `/`
served the compiled React HTML. The temporary process was terminated afterward.
The existing backend on port 8000 and existing database were left in place.

Not exercised: installation into a fresh `.venv-replit`, a fresh Replit `npm ci`,
availability of Replit's requested runtime modules, actual import/preview,
hosted persistence, live Groq calls or a new browser walkthrough. The startup
check used local installed dependencies. These are preparation checks, not proof
of a working hosted Replit app. Full remaining UI specification work is still
pending as documented in `SPEC_INCREMENT_1.md`.
