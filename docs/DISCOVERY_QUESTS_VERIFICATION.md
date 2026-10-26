# Shared Discovery Quests verification

Verified October 24, 2026. Scope: Discovery Quests and additive quest reward metadata. Existing routes, other page implementations, SQLite schema, LangGraph workflows and Streamlit fallback are retained.

## Implemented behavior

- One React page and shared view model handle new, partial and completed explorers. Saved API responses determine answered quests, the first incomplete quest, selected answers and Discovery Clues. Backend confirmation status determines whether updated clues require reconfirmation. Local state holds only the current view and unsaved input.
- Completed quests show the saved answer in read-only mode. Explicit Edit answer opens a prefilled draft; Cancel edits discards it without an API request; Save changes explicitly saves a revision. Unchanged drafts cannot be saved. Leaving a dirty draft prompts for an explicit discard.
- Discovery Clues show each saved choice, its source interest clue and saved timestamp. They are exploration prompts, not personality diagnoses or fit scores.
- The API projects quest XP from the full persisted event history, including events outside the recent-30-event display window. New completion events record the existing 20-XP reward; revisions record zero. Duplicate completion requests are rejected, and saving the same revision again is a no-op.
- Editing a confirmed explorer's answer retains the prior confirmed profile snapshot and all saved roadmap versions. Existing backend gates reject exploration and new roadmap proposals/saves until the updated profile is confirmed.
- No database reset, schema migration or historical event rewrite was performed. Existing canonical API events without explicit reward metadata use the established 20-XP policy; unknown imported receipts with untraceable rewards produce an unknown total, which the UI omits.

## Changed source and test files

| File | Change |
| --- | --- |
| `careerquest/quests.py` | Shared constant for the existing quest reward. |
| `careerquest/discovery.py` | Read-only persisted discovery progress and reward projection. |
| `careerquest/api.py` | Additive discovery response metadata and explicit XP receipt payloads. |
| `frontend/src/discoveryJourney.js` | Shared persisted-answer view model. |
| `frontend/src/discoveryEditor.js` | Unsaved edit/cancel/reset reducer. |
| `frontend/src/pages/DiscoveryQuests.jsx` | Shared quest, saved-answer, editing and clue views. |
| `frontend/src/pages/discovery.css` | Page-scoped responsive styling. |
| `frontend/src/components/UnsavedChanges.jsx` | Optional dialog description and accurate quest discard copy; profile behavior retained. |
| `tests/test_discovery_flow.py` | Four API/persistence/reward/history/gate tests. |
| `frontend/tests/discovery-journey.test.js` | Five persisted-state and reload model tests. |
| `frontend/tests/discovery-editor.test.js` | Two draft/cancel/reset tests. |
| `frontend/tests/discovery-render.test.js` | Three rendered new/partial/completed state tests. |

The React production build was regenerated. This report and `docs/test-evidence/discovery-*` files contain verification artifacts.

## Exact verification commands and results

Run from `/Users/vishalakosaraju/Downloads/careerquest_ai`:

```sh
.venv/bin/python -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-baseline-pycache .venv/bin/python -m compileall -q careerquest app.py tests
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
```

| Check | Actual result |
| --- | --- |
| Python suite | 40 passed; 0 failures; 0 skips. |
| Python compilation | Passed; exit 0. |
| Frontend suite | 55 passed; 0 failures; 0 skips. |
| React production build | Passed; exit 0. |
| Normal API startup after restart | `/api/health` returned `status: ok`, `agent_engine: langgraph`. |

Existing test expectations were not changed. Tests use temporary SQLite databases. No new frontend dependency was added.

## Actual browser walkthrough

Chrome exercised the production build against a separate temporary database on localhost port 18094. The fictional explorer was **Orbit Discovery Demo**, Grade 11. The normal application database was not used for these mutations.

| Scenario | Observed result |
| --- | --- |
| New explorer | Quest 1 had no selected answers and zero quest XP. |
| Partial explorer | After saving Quest 1, reload and the existing next-action navigation opened unanswered Quest 2. Revisiting Quest 1 showed its saved selection, with choices disabled until Edit answer. |
| Completed explorer | All three saved choices appeared in Discovery Clues with 60 quest XP. Revisit used the same component and saved records. |
| Cancel edit | Changed the draft, then cancelled. The saved choice returned; the complete API state matched the pre-edit state and the quest-write request count remained unchanged. |
| Dirty navigation | Changing quests with an unsaved draft opened the discard dialog. Keep editing retained the editing view; explicit discard opened the selected saved quest. |
| Save revision | Changed Quest 1 from Build a mini-app to Sketch an invention. Its saved choice and clue updated, confirmation became false, and quest XP stayed 60. |
| History preservation | The earlier confirmed profile snapshot remained identical. All rows for roadmap versions 1 and 2 remained identical, including IDs, content and timestamps. |
| Duplicate protection | Repeating the same revision returned unchanged API state. Duplicate initial completion returned HTTP 409 in the automated test. |
| Direct API gates | Unconfirmed `/explore`, `/roadmap/propose` and `/roadmap/save` requests each returned HTTP 409 and did not mutate state. |
| Reload after revision | Updated choice and reconfirmation requirement survived reload. |
| Reconfirmation | Confirming the updated profile enabled a personalized proposal again (HTTP 200), retaining both saved roadmap versions. Quest XP remained 60. Existing confirmation policy separately awarded 10 XP, so total XP changed from 70 to 80. |
| Keyboard | Arrow keys changed the draft radio selection; Enter on Cancel edits restored the persisted selection. Radio groups, selected/disabled states, progress label, status messages and button names were present in the accessibility tree. |
| Responsive | Completed clues at exact 375, 768 and 1280 CSS-pixel iframe widths had document scroll width equal to viewport width: no horizontal overflow. Saved-answer view also had no horizontal overflow at 375px. Cards used one column at 375/768 and three at 1280. |

Responsive checks used an isolated HTML iframe fixture to avoid Chrome zoom affecting the requested CSS widths. Screenshot framing can include the outer fixture. The temporary server was stopped after verification.

The normal backend was restarted on localhost port 8000 to load the additive metadata. The normal SQLite database file hash was identical before and after restart and a read-only legacy-profile request. Its existing explorer also displayed the saved answers and Discovery Clues in the browser; no answers were submitted there.

## Evidence and limits

- Screenshots: `test-evidence/discovery-shared-new.jpg`, `discovery-shared-complete.jpg`, `discovery-shared-editing.jpg`, `discovery-shared-reconfirmation.jpg`, `discovery-shared-375.jpg`, `discovery-shared-768.jpg`, `discovery-shared-1280.jpg`, `discovery-shared-live.jpg`.
- API assertions: `test-evidence/discovery-shared-api.json` and `discovery-shared-reconfirmed.json`.
- Responsive measurements: `test-evidence/discovery-responsive.json`.
- Restart check: `test-evidence/discovery-backend-restart.json`.

No failing or skipped automated tests remain. A VoiceOver session, native reduced-motion setting, live Groq/model calls and a separate Streamlit launch were not exercised in this scoped verification. Accessibility-tree and keyboard checks do not establish full assistive-technology conformance. Other pages received regression coverage from the existing suite, not a new full application walkthrough.
