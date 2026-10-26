# Groq Discovery Guide — implementation and verification

Verified October 24, 2026 (Pacific). Scope stops at the Discovery Guide. No new provider, model setting, credential or dependency was introduced.

## Delivered behavior

After the three persisted quests, the React Discovery Quests page requests a Discovery Guide. The same component serves new quest completers and returning explorers. It automatically requests a fresh version when the saved-response hash changes, including after an explicit answer edit; merely visiting or reloading returns the cached version.

The guide presents **What You Chose**, **What This Might Suggest**, **What You Could Try Next**, and zero to three Career Worlds. Each interpretation, activity and world cites saved choice IDs; the UI shows those references as the actual quoted choices. The greeting uses the backend nickname and grade with a neutral nickname fallback.

A separate `groq_discovery()` function uses the existing Groq endpoint, backend key and `GROQ_MODEL` setting (default `openai/gpt-oss-120b`). The existing action-selection function, allowlist, LangGraph graph and tool contracts were not changed. [Groq's structured-output documentation](https://console.groq.com/docs/structured-outputs) was consulted for the strict schema contract.

### What the model generates, and what Python controls

Groq selects and orders bounded narrative building blocks and catalogue worlds in a separate strict JSON output. Python checks the complete output and renders approved tentative wording. This intentionally does **not** accept unrestricted model prose: schema compliance alone cannot establish that a free-form achievement, aptitude claim or diagnosis is true.

Validation requires all three exact saved choice/ID pairs, no duplicates or extra fields, valid interest/activity IDs tied to the supporting choices, at most three unique Career World IDs, and matching catalogue tags for **every** supporting choice. Only the existing career records `bioengineering`, `software`, `design` and `environment` are eligible; generic college/aid/checklist records are not presented as Career Worlds. Metadata and URLs come from the catalogue, not the model. This closed vocabulary cannot introduce achievements, diagnoses, aptitude/fit scores or admissions predictions.

The model receives only grade and the three backend-loaded saved choices/IDs plus approved vocabulary. The backend nickname is used in presentation and is not sent. Corrections, feedback, profile history, roadmap history and XP are not sent. Only fictional explorers are supported.

### Persistence and integrity

Two additive SQLite tables store story versions and feedback. Each story stores its source-answer snapshot, SHA-256 source-response version, configured model identifier, generation status (`pending`, `groq` or `fallback`), safe error class, timestamp and rendered structured content. The current saved-answer hash determines staleness on every read; old stories are not rewritten or deleted. Feedback revisions are stored separately; the UI displays the latest feedback for each story.

Yes / Somewhat / Not really feedback and an optional correction (500 characters maximum) require an explicit save. Feedback never confirms a profile or awards XP. Existing profile confirmation and roadmap save gates remain intact. A changed quest still requires profile reconfirmation before personalized research or new roadmap proposals/saves. Generation and feedback never change XP or historical roadmap records.

Generation attempts are atomically reserved in SQLite **before** network I/O: five per explorer/hour and thirty total/hour, including failures. Cache replays make no model request. Concurrent requests for an explorer receive HTTP 409 while its request is pending. An interrupted reservation can be retried after sixty seconds. Explicit fallback retries create another version and consume a limit slot. Feedback changes are capped at twenty per explorer/hour; identical repeated feedback is a no-op. Limits persist across workers/restarts. HTTP 429 includes `Retry-After: 3600`.

Requests use an 18-second socket timeout, a 2,400-token completion limit and a 48,000-byte response cap. Missing credentials, transport/model errors, incomplete output, malformed JSON and invalid evidence produce a persisted **Deterministic Discovery Summary · Not AI-generated**. No alternative model/provider is silently selected. Only an error class is stored, not credential-bearing upstream exception text.

## Changed files

| File | Change |
| --- | --- |
| `careerquest/discovery_guide.py` | Provider request, closed schema/domain validation, rendering, snapshots, limits, cache/history and feedback service. |
| `careerquest/store.py` | Two additive tables and a profile/version index; existing table definitions and reward functions retained. |
| `careerquest/api.py` | Additive `discovery_guide` profile state; POST generation and feedback endpoints with validated bodies and 409/429 handling. |
| `frontend/src/components/DiscoveryGuide.jsx` | Shared story/summary view, source choices, provenance, feedback, retry and version history. |
| `frontend/src/pages/DiscoveryQuests.jsx` | Mount guide after all quests, disclose cloud generation, refresh after answer revisions. Existing quest edit/cancel/save behavior retained. |
| `frontend/src/pages/discovery.css` | Scoped guide, feedback and responsive world-card styling. |
| `tests/test_discovery_guide.py` | Eleven mocked provider/API/persistence/validation/rate-limit/in-flight-edit tests. |
| `frontend/tests/discovery-guide-render.test.js` | Four story/fallback/stale/feedback rendering tests. |
| `scripts/smoke_discovery_guide.py` | Explicit, reproducible live smoke test using a temporary fictional DB. |
| `README.md` | Updated provider boundaries, behavior, limits and smoke-test instructions. |

This report, generated `frontend/dist` assets, and `docs/test-evidence/discovery-guide-*` files are also verification outputs. `careerquest/agent.py`, `careerquest/graph.py`, `.env`, catalogue content, Streamlit and the other page implementations were not changed. Existing test expectations were not changed.

## Commands and actual results

Run from `/Users/vishalakosaraju/Downloads/careerquest_ai`:

```sh
.venv/bin/python -m unittest tests.test_discovery_guide -v
.venv/bin/python -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-guide-pycache .venv/bin/python -m compileall -q careerquest app.py tests scripts/smoke_discovery_guide.py
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
.venv/bin/python scripts/smoke_discovery_guide.py --live --output docs/test-evidence/discovery-guide-live.json
```

| Check | Actual final result |
| --- | --- |
| New backend tests | 11 passed, all Groq calls mocked. |
| Full backend suite | 51 passed; zero failures/skips. Includes existing routing, LangGraph, SQLite, XP and confirmation tests. |
| Full frontend suite | 59 passed; zero failures/skips. Four new tests plus existing 55 tests. |
| Python compilation | Passed, exit 0. |
| React production build | Passed, exit 0. |
| **LIVE Groq smoke** | **Passed**, one actual generation request using `openai/gpt-oss-120b`; no provider mock. |
| Local API restart | Health `ok`, engine `langgraph`; new profile-state field available. |

During development the new tests caught an SQL placeholder-count defect and saved-feedback input initialization defect. Both were corrected. A new render-test assertion was made independent of HTML attribute order while retaining the checked-selection requirement. No unresolved failures remain and no pre-existing assertions were weakened.

### Mocked tests

Coverage includes valid strict output/minimal prompt, malformed JSON, timeout, incomplete output, oversized response, missing key, unsupported world, fabricated saved choice, invalid evidence, invented free-text fields, duplicate choices, world/tag mismatch, too many worlds, feedback validation/persistence/deduplication, stale-story/history preservation, edited confirmed-profile/roadmap integrity, no XP changes, confirmation bypass attempts, cache replay, per-explorer/global request limits, feedback limits, and source changes while generation is in flight. A model response invalidated by an in-flight quest edit remains stale; it cannot replace the current answer snapshot.

### Live inference — explicitly separate from mocks

The smoke script created **Comet Fictional Smoke**, Grade 10, in a temporary SQLite database. Saved choices were Build a mini-app, Analyze the data and Build something. The actual Groq response passed exact-choice and evidence validation and selected **Biomedical Engineering**. Only one suggestion was returned, within the zero-to-three contract. Story content and IDs are recorded in `test-evidence/discovery-guide-live.json`.

A cached replay reused the same story; Somewhat feedback persisted; quest XP remained 60; profile confirmation remained false; a direct roadmap-proposal request returned HTTP 409. The normal database was not used. This live check ran before a later server-rendered sentence was polished from “might be a reason to explore” to “might spark curiosity about”; the provider/schema contract did not change, and the live evidence retains the actual original wording.

### Browser walkthrough — deterministic fallback, not live inference

Chrome used an isolated server on localhost port 18095 with the Groq key deliberately unavailable and a separate temporary database. **Nova Guide Demo**, Grade 10, completed all three quests. A visibly labeled deterministic summary appeared automatically with quoted saved choices and catalogue worlds. Somewhat feedback plus a fictional correction persisted after reload. Revisiting discovery did not create another story version.

Editing Quest 1 from Sketch an invention to Build a mini-app created version 2 automatically. Version 1 became stale and remained inspectable with its original choice and feedback. The new guide used the revised choice and did not inherit the old version's feedback. Backend readback confirmed exactly two versions, 60 quest XP/total XP and no profile confirmation. The existing quest editor continued showing the selected saved answer.

At exact iframe widths 375, 768 and 1280 CSS pixels, document scroll width equaled viewport width. World cards used one column at 375/768 and three at 1280; the correction field remained inside the page. These are browser layout observations, not native-device or full accessibility certification.

The normal localhost backend was restarted for the additive endpoints/schema. Every row in the existing `profiles`, `events`, `plans` and `runs` tables was compared before and after startup/readback and remained identical: 5 profiles, 40 events, 7 roadmap versions and 42 runs at that check. No database reset or synthetic record replacement was performed.

## Evidence and limits

- `test-evidence/discovery-guide-live.json`: actual live inference, model, story, cached replay, feedback and gate results.
- `test-evidence/discovery-guide-browser.json`: isolated fallback/history/XP readback.
- `test-evidence/discovery-guide-responsive.json`: 375/768/1280 measurements.
- `test-evidence/discovery-guide-restart.json`: normal API restart and original-row integrity.
- Screenshots: `discovery-guide-fallback.jpg`, `discovery-guide-history.jpg`, `discovery-guide-375.jpg` in `test-evidence/`.

The live provider test was API-based; the interactive browser walkthrough deliberately tested the fallback. Native VoiceOver, native reduced-motion settings and a new Streamlit launch were not exercised. The Discovery Guide is integrated into React, not newly added to Streamlit. Career/college research and roadmap contents remain curated/deterministic; live verified research and unrestricted narrative generation are not implemented. No production authentication or real-student handling is claimed.
