CareerQuest specification implementation — increment 1

The full [UI/UX specification](https://docs.google.com/document/d/1eKs2o8w3tMGNiXEEtQmLSXZwJwCepsIrgDkrxufst2w/edit) was accessible and read, including all 17 sections (12,936 text characters). Source revision `AHj4eMSLdAtuTm6FKyl2P2XjAXRYDwoC1PSCCy0xhc6O03pg7oSuGNXK8JugIiGK_2ZgQzaQrBX2YPIRdzpsda1pcYZsQolEVEwcN7WNa_k` is recorded with the full text in [the local specification reference](reference/UI_SPECIFICATION.txt). The source is a target design, not evidence of implemented features.

This checkpoint covers Dashboard, Discovery Quests, Explorer Profile, and the shared navigation/state needed by them. Work stops at this report before the remaining-page increment.

| Area | Implemented and verified in this increment |
| --- | --- |
| Navigation | Six named primary pages in specification order; current-page indicator; fictional nickname/grade, persisted XP and quest count; compact mobile menu |
| Dashboard | Distinct entry/resume page; avatar, grade, XP, quest count, confirmed/unconfirmed interest labels, dynamic Continue My Adventure, graphical map, topic teaser cards, latest saved roadmap summary, recent activity |
| Discovery Quests | Three illustrated scenario cards, selectable radio choices, keyboard arrows, Previous/Continue, progress, neutral feedback, first-completion XP, explicit profile unlock, and editable saved answers |
| Explorer Profile | Separate actual-answer facts and inferred suggestions; editable/custom interests; reject suggestions; uncertainty option; learning style; goal; optional correction; explicit confirmation; confirmed read view and Edit Profile |
| Draft safety | Event-backed unconfirmed versions, source quest snapshots/timestamps, preserved previous confirmed fields, stale-version rejection, server-side research/roadmap gate until reconfirmation |
| Unsaved edits | Navigation dialog protects quest choices and profile edits; saved draft can be kept before navigation; incomplete custom-interest text cannot be silently dropped by a save; browser unload warning for unsaved edits |
| Reward integrity | Quest edits and unchanged replay add no quest XP. Reopening and reconfirming an unchanged profile also adds no extra XP |

Implementation files changed or added:

- `careerquest/api.py`: quest revision mode on the existing response endpoint, profile draft endpoint, draft-aware confirmation and profile state.
- `careerquest/profiles.py`: event-based current quest answers, draft/confirmed versions, source evidence and idempotent rewards. No database schema change.
- `frontend/src/App.jsx`: shared-shell/page integration, profile draft persistence, protected navigation, and existing remaining-page wiring.
- `frontend/src/components/AppShell.jsx`: six-page navigation, StudentHeader and XPProgress.
- `frontend/src/components/UnsavedChanges.jsx`: focus-trapping native dialog with explicit save/stay/leave actions.
- `frontend/src/components/Shared.jsx`: readable quest revision and profile draft activity labels.
- `frontend/src/pages/Dashboard.jsx`, `DiscoveryQuests.jsx`, `ExplorerProfile.jsx`: reusable page/component implementation.
- `frontend/src/journey.js`: draft-aware restored values and Dashboard routing.
- `frontend/src/spec.css`, `frontend/src/main.jsx`: violet/teal education-game tokens, accessible focus/touch states, responsive styles and stylesheet entry.
- `tests/test_api.py`, `frontend/tests/journey.test.js`: added meaningful regression scenarios; previous expectations preserved.
- `README.md`, this report, specification reference, and screenshots/state evidence.

Exact automated verification commands, from the project root:

```sh
.venv/bin/python -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-baseline-pycache .venv/bin/python -m compileall -q careerquest app.py tests
PYTHONPATH=. .venv/bin/python scripts/smoke_core.py
```

From `frontend/`, using the Node runtime installed during baseline verification:

```sh
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm run build
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm test
```

Final results: **31 Python tests passed; 7 frontend tests passed; zero failures or skips.** Production build and backend compilation passed. The offline core smoke test passed. The Python suite executed the real LangGraph integration, allowlist/local provider endpoint validation, failure preservation, and SQLite persistence checks. No new dependencies were required.

Browser and live local API walkthrough:

1. Created one new fictional Grade 11 explorer, **Spec Phase One Demo**, ID `ff8f86ba-0460-469a-bc94-8bf4062ef2ac`. Existing explorers were not edited.
2. Used native radio-button keyboard arrows to choose Investigate a science mystery, then Continue. Received 20 XP.
3. Used Previous to revise that saved choice to Build a mini-app. XP stayed at 20; the original response and revision remained in history.
4. Completed Analyze the data and Research and test ideas. Reached 60 XP and the explicit Unlock Explorer Profile screen.
5. Dashboard resumed at Review & confirm rather than personalized research. The profile facts showed the revised actual answer.
6. Checked uncertainty/rejection controls, restored suggestions, added robotics, chose Creative activities and Try a mini-project, and entered a synthetic correction.
7. Attempted navigation away; the dialog offered to keep editing, save a draft, or explicitly leave without saving. Save draft & leave retained the fields. After reload, all saved draft values returned.
8. Confirmed profile version 1. Reached 70 XP and Dashboard routed to Career Worlds.
9. Used Edit Profile to create unconfirmed version 2. Direct HTTP POST checks to `/api/profiles/ff8f86ba-0460-469a-bc94-8bf4062ef2ac/explore` with `{"message":"Explore careers"}`, `/roadmap/propose` with `{}`, and `/roadmap/save` with `{"plan":{}}` each returned HTTP 409. No research/model call ran.
10. Added design, saved the draft, and confirmed version 2 on mobile. Reached 80 XP.
11. Reopened as version 3 to verify an unadded custom-interest field is protected. The save action explained that the interest must be added or cleared. Clearing that uncommitted text and reconfirming the otherwise unchanged profile preserved 80 XP. A repeated confirmation also left XP/history unchanged.
12. Verified reload and backend restart retain the test profile and its source answer snapshots, timestamps, corrections and earlier versions.

Responsive checks measured page width equal to viewport width at **375px, 767px (approximately the 768px target), and 1280px**. Mobile navigation exposed all six page links. Keyboard radio selection and modal focus trapping were exercised. Existing reduced-motion CSS is retained, but an operating-system reduced-motion preference was not activated during this browser run. No full assistive-technology audit is claimed. Browser console error readback was empty.

Evidence:

- [Final Dashboard](test-evidence/spec-increment1-dashboard-final.jpg)
- [Discovery Quests](test-evidence/spec-increment1-quests.jpg)
- [Profile draft with actual answers and suggestions](test-evidence/spec-increment1-profile.jpg)
- [Profile on mobile](test-evidence/spec-increment1-profile-mobile.jpg)
- [Dashboard on mobile](test-evidence/spec-increment1-dashboard-mobile.jpg)
- [Final confirmed profile](test-evidence/spec-increment1-profile-confirmed.jpg)
- [Unconfirmed API state](test-evidence/spec-increment1-unconfirmed-state.json)
- [Final persisted API state](test-evidence/spec-increment1-final-state.json)

Remaining work is explicitly not claimed complete:

- Career Worlds retains its existing offline exploration and citations. Full world-detail drawers, saved careers and the specification's expanded Agent Activity panel remain for the next increment.
- My Roadmap retains its existing five-item template, proposal/save boundary and versioned persistence. Grouped near-term/school-year/future milestones, effort, editable completion and a browsable version history remain pending.
- Existing activity timeline content is now under the correct My Journey navigation link; saved-career views, previous/current interest comparison and expanded reflection/version UX remain pending.
- Optional Groq action selection is preserved as previously requested, replacing the specification's legacy Ollama wording. No live model request was needed for these first three pages. Retrieval remains curated/offline and keyword-based. Live verified admissions research and semantic retrieval are not implemented.
- LangGraph code and existing SQLite history were preserved; no durable graph checkpoint/interrupt behavior is claimed. The Streamlit fallback source was unchanged and was compiled, but its native UI was not launched during this increment.
- Avatars/profile switcher remain browser-local demo behavior; there are no authenticated production student accounts.

The application remains available at http://127.0.0.1:8000/. A dedicated synthetic verification profile is selected for review. No database was reset or migrated, no prior profile was deleted, and no secret was displayed. The next increment is the remaining three pages and expanded Agent Activity behavior after this checkpoint report.
