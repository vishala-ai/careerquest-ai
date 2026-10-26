# Explorer Profile: confirmed-branch diagnosis and three-state refinement

Verified 2026-10-25. All students used for verification are fictional.

## Exact cause

The original Version 4 browser tab was using the current production build, not an obsolete component or stale frontend asset.

- `App.jsx` imports one `pages/ExplorerProfile.jsx` and mounts it when `page === 'confirm'`.
- Before this change, `ExplorerProfile.jsx` used `state.confirmed ? <plain confirmed panel> : <ProfileDiscoveryReview .../>`. Consequently, a confirmed profile never mounted the component containing Yes / Somewhat / Not really. The confirmed branch still rendered **My confirmed Explorer Profile**, a plain definition list and raw correction text.
- The backend derives `confirmed` from persisted event order: its latest confirmation must follow the latest profile draft or revised quest. This was not a client-only flag.
- The actual original tab showed **Confirmed profile · Version 4**, 100 XP and zero feedback radios, and loaded `/assets/index-D0917bLY.js`.
- Uvicorn served FastAPI on `127.0.0.1:8000`. FastAPI mounts `frontend/dist` through `StaticFiles`. Both its HTML and JavaScript matched the files on disk byte-for-byte. The served bundle contained both the feedback component and the plain confirmed panel.
- No listeners were found on the configured/common Vite development/preview ports 5173 or 4173. The observed tab was using port 8000, not a Vite dev server.

The design gap was the unchanged confirmed-state presentation. The feedback UI existed but was correctly restricted to an unconfirmed profile. Forcing feedback onto confirmed profiles would repeat review; this change instead gives confirmation its own completed-state design.

## Rendering conditions

| State | Persisted condition | Current rendering |
| --- | --- | --- |
| Prerequisites incomplete | No Explorer or `!state.quest_complete` | Existing quest/setup gate, unchanged |
| New unconfirmed profile | Quests complete, `!state.confirmed`, no earlier `profile_preferences` | Discovery interpretation, directly editable interest chips, feedback controls, staged edits and explicit confirmation |
| Confirmed profile | Quests complete and `state.confirmed` | Personalized purple summary, interest cards, learning preference, goal, confirmed badge, Edit Profile and Explore Career Worlds; no repeated feedback radios |
| Editing/reconfirmation | Quests complete, `!state.confirmed`, earlier `profile_preferences` exists | Saved values and correction editor open immediately; save and review revised interpretation, then explicitly reconfirm |

`isReconfirmation()` uses these backend-returned records. Edit Profile retains the existing server draft operation, which invalidates personalized actions until reconfirmation. Feedback, profile versioning, handoff validation and XP policies were not replaced.

## UI changes

- The confirmed summary uses the saved nickname, illustrated interest cards, a compass motif and the existing purple/white theme. No interests, student names or XP totals are hardcoded.
- Technical profile/handoff versions and the original saved note are inside closed **Saved profile details**. A missing handoff is not fabricated or backfilled.
- Corrections are transformed for presentation only. First-person notes can lose their fictional-demo prefix; the existing instructional note about revisiting career goals gets a short student-friendly phrase. Unrecognized notes receive neutral wording rather than an invented interpretation. Original wording stays available in secondary details and audit history.
- Unconfirmed interest chips now open the same existing editor on a change. Saving produces an unconfirmed proposal, not a confirmation. Durable manual differences can be reconstructed from saved drafts, prior confirmed preferences and actual quest records after reload.
- Editing opens the saved interests, activities, goal and exact correction text. Unchanged drafts can advance with **Review Saved Profile**; changed drafts use **Save Changes & Review Proposal**. A fresh Yes reveals **Reconfirm My Explorer Profile**.
- Scoped CSS overrides the global profile typography rules that previously won in the cascade. Measured titles are 36px desktop/tablet and 28px mobile; confirmed body text is 18px desktop and 17px mobile, with 21px interest titles.
- All new CSS is scoped under `.spec-shell .spec-page.explorer-profile-page`. Other pages, navigation, backend services, Groq configuration, agent workflows and database schema were not changed.

## Actual results

| Check | Result |
| --- | --- |
| Python backend suite | **111 passed, 0 failures, 0 skips** |
| Frontend suite | **94 passed, 0 failures, 0 skips** |
| React production build | Passed, Vite 5.4.21 |
| Backend compilation | Passed |
| Browser: unconfirmed | Interpretation, editable interests, all three feedback choices and explicit confirmation verified |
| Browser: confirmed | New cards, preference/goal, confirmed badge, friendly note, Edit/Explore and collapsed audit details verified |
| Browser: editing | Saved values/correction, refreshed interpretation, changes, and explicit reconfirmation verified |
| Direct personalized API calls during editing | `/explore` and `/roadmap/propose` both returned **HTTP 409**; API state unchanged |
| Database preservation | Every pre-existing normal database row matched before/after verification |
| Existing Version 4 tab | Refreshed and verified with new summary, three saved interests and unchanged 100 XP |

Commands run from the repository root:

```sh
.venv/bin/python -m unittest discover -s tests -q
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-profile-states-pycache .venv/bin/python -m compileall -q careerquest app.py tests
```

The frontend suite adds five presentation/domain tests and four state-render tests; its old confirmed-panel expectation was updated to the requested card summary. Existing backend expectations were unchanged. Tests cover correction/source preservation, safe unknown-note presentation, backend-derived state distinctions, saved differences after reload, confirmed/uncertain cards, inline interests and prefilled reconfirmation.

The isolated browser used localhost:18100, temporary fictional storage and explicitly labeled deterministic fallback, not live Groq. **Nova Fictional** completed quests at 60 XP, saved an art proposal, confirmed at 70 XP, edited to add coding and reconfirmed at 80 XP. Saving the edit itself kept XP at 70 and did not unlock research. Both original confirmed correction strings and all raw quest choices remained in SQLite. **Comet Fictional** independently verified the final new/unconfirmed rendering. The test server and test tab were closed afterward.

All three final states were checked at actual CSS widths **375px, 768px and 1279px**, with document width equal to viewport width. The last approximates 1280px because of the browser's existing zoom. Keyboard confirmation and audit disclosure worked; the browser error log was empty. No full assistive-technology audit or live inference test is claimed in this UI-only increment.

The original app now serves `/assets/index-C-ME4Mhi.js` and `/assets/index-Cm0lq9YF.css`; the new JavaScript again matches the built file byte-for-byte. No backend restart was required because only frontend source changed. The original Version 4 tab was refreshed and left on the updated profile summary.

## Changed files

- `frontend/src/pages/ExplorerProfile.jsx`: explicit three-state presentation and inline interest-editor wiring.
- `frontend/src/components/ExplorerProfileSummary.jsx`: new confirmed summary and secondary saved-record details.
- `frontend/src/components/ProfileDiscoveryReview.jsx`: saved-value editing entry, staged inline edits, friendly note display and explicit reconfirmation wording.
- `frontend/src/profilePresentation.js`: presentation-only correction wording, reconfirmation predicate and persisted-draft comparison.
- `frontend/src/pages/explorer-profile.css`: scoped purple profile styling and readable responsive typography.
- `frontend/tests/profile-review-render.test.js`: updated confirmed branch and four additional UI-state checks.
- `frontend/tests/profile-presentation.test.js`: five new presentation and persistence-derived state tests.
- This report and `docs/test-evidence/profile-states-*`.

No backend, database, model-provider, Career Research Agent, Discovery Quests, Welcome, roadmap or journey source files changed in this increment. No database reset, record overwrite or new real student data.

## Evidence

- [Original source/server/browser diagnosis](test-evidence/profile-states-diagnosis.json)
- [Three-state browser and font measurements](test-evidence/profile-states-browser.json)
- [Editing personalization gates](test-evidence/profile-states-gates.json)
- [Database/history and final asset preservation](test-evidence/profile-states-preservation.json)
- [Refreshed original tab](test-evidence/profile-states-existing-browser.json)
- [Unconfirmed profile](test-evidence/profile-states-unconfirmed.jpg)
- [Confirmed summary](test-evidence/profile-states-confirmed.jpg)
- [Saved-value editing](test-evidence/profile-states-editing.jpg)
- [Original Version 4 record with new design](test-evidence/profile-states-existing-version4.jpg)
