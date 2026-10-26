# Welcome / Adventure Home refinement

The Student Journey cards were subsequently replaced with the connected
[Adventure Trail](STUDENT_TRAIL_VERIFICATION.md). This report records the preceding
Welcome refinement; its hero and setup behavior remain in place.

Refined the existing Welcome page in place. Its purple/white palette, hero grid,
compass illustration, orbit/sticker artwork, rounded cards and spacing remain.
Only Welcome presentation, its state projection and its setup integration changed.
No other page implementation, backend service, schema, database record, LangGraph
workflow, Streamlit fallback or existing test expectation was changed.

## Changed files

- `frontend/src/pages/Welcome.jsx`: saved-name greeting (`Hi, {nickname}! 👋`),
  next-action heading, requested three-quest instruction, inline first-time
  nickname/grade setup, state-aware CTA, secondary Switch Explorer, and five-stage
  Discover → Confirm → Explore → Plan → Reflect journey.
- `frontend/src/pages/welcome.css`: scoped refinements; supporting text 17–18px,
  setup fields, active/completed/locked card states and responsive five-stage grid.
  Existing hero artwork and reduced-motion rules are retained.
- `frontend/src/welcomeJourney.js`: new read-only projection of the backend
  profile response, with five-stage completion, availability and next activity.
- `frontend/src/App.jsx`: Welcome-only setup calls the existing profile endpoint,
  hydrates saved state and opens Quest 1 directly. A missing saved explorer stays
  on Welcome setup when loaded from Welcome. Existing profile-page creation and
  all other page handlers are unchanged.
- `frontend/tests/welcome-journey.test.js`: six new domain regression tests.
- This report and `docs/test-evidence/welcome-refined-*` evidence.

The Welcome CTA follows persisted quest count, completion, confirmation,
research runs, saved roadmap and reflections. It reads no browser-only completion
flags. Labels/destinations are Start My First Quest / Discovery, Continue Quest
2 or 3 / first unfinished quest, Review My Explorer Profile / profile review,
Explore Career Worlds / exploration, Build My Roadmap / planning, and Reflect
on My Journey / the actual reflection form. After all five stages are complete,
students can explore again. Editing a confirmed profile makes Confirm active
again and locks personalized activities while preserving prior history.

## Commands and actual results

From the project root:

```sh
.venv/bin/python -m unittest discover -s tests -v
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
```

**35 backend tests passed; 20 frontend tests passed; React production build
passed. Zero automated failures or skips.** No dependencies were added. Existing
allowlist, failure handling, confirmation gate, SQLite persistence and unique-XP
checks remained passing. The six new tests cover setup/first-quest routing,
nickname fallback, each CTA transition, reload-equivalent restored data,
updated-profile gating, missing earlier exploration despite a saved plan,
proposal/save separation and read-only XP integrity.

## Browser and API verification

A separate localhost:18084 process used a newly created temporary synthetic
SQLite file. No existing database was reset or populated by these checks.
The process was launched with the repository `.venv/bin/python` and
`-m uvicorn careerquest.api:app --host 127.0.0.1 --port 18084`, with
`CAREERQUEST_DB` pointing to that temporary file.

1. First visit showed the new welcome, nickname field, grade selector and
   fictional-data checkbox. The first-quest button stayed disabled until setup
   was valid. Enter submitted fictional **Nova Welcome Test**, Grade 10, and
   opened the actual Quest 1 rather than a landing page.
2. Saved Quest 1, returned to Welcome and reloaded. Greeting was
   **Hi, Nova Welcome Test! 👋**; CTA was **Continue Quest 2**; Discover showed
   1 of 3 saved quests. Enter opened the actual second quest.
3. Completed quests 2 and 3. Discover displayed Complete; Confirm became active;
   Review My Explorer Profile opened the existing review form.
4. Confirmed the profile. Explore became active; Explore Career Worlds opened
   the actual career exploration page. Ran deterministic offline exploration,
   returned after its completion and saw Build My Roadmap.
5. Build My Roadmap opened the actual roadmap proposal page. Explicitly saved
   the proposal, returned to Welcome, and saw four completed stages with Reflect
   active. Reflect on My Journey opened the actual reflection form.
6. Revisited completed Discover from its card and replayed the same saved first
   quest response. XP stayed at **70**, with three quests, one successful research
   run and saved roadmap version 1 intact.
7. Switch Explorer opened the existing explorer-switch/create page. Keyboard
   Enter activated primary and secondary actions. Journey controls expose an
   ordered list, current-step state, explicit completion text and native disabled
   states. The destination H1 receives focus after Welcome navigation.
8. Saved an unconfirmed edit only for the isolated test explorer. On reload,
   Review My Explorer Profile took priority and Confirm became active again.
   Direct exploration/proposal/save calls each returned HTTP 409. Reconfirmed
   the unchanged draft and the Reflect CTA returned. No extra quest XP was awarded.
9. Opened the existing localhost:8000 application with its existing selected
   fictional explorer and verified the saved nickname greeting and refined UI.
   No write was made to that normal application's records. Final browser
   console error/warning readback was empty; viewport overrides were reset.

Measured responsive widths: **375px, 769px (approximately the 768px tablet
breakpoint), and 1280px**. Each document scroll width matched its actual viewport
width; no horizontal overflow was measured. The nearby 767px layout was also
checked. Titles were 28px at mobile and 36px at tablet/desktop. Supporting
paragraphs, stage statuses and controls measured 17px at mobile and 17–18px on
larger screens. First-time mobile setup fields measured 17px. Chrome's zoom
caused integer viewport overrides around the tablet target to measure 767/769px;
no claim of an exact 768px run is made for this increment.

Evidence:

- [Returning explorer and five-stage journey](test-evidence/welcome-refined-1280.jpg)
- [Returning mobile page](test-evidence/welcome-refined-375.jpg)
- [First-time mobile setup](test-evidence/welcome-refined-setup-mobile.jpg)
- [Tablet page](test-evidence/welcome-refined-tablet.jpg)
- [Measured responsive values](test-evidence/welcome-refined-responsive.json)
- [XP, saved history and direct confirmation gates](test-evidence/welcome-refined-api.json)

No live model request was used; research remains curated/offline. Full screen
reader speech and OS reduced-motion preference activation were not exercised.
Existing loading/error/retry rendering remains, but a new outage simulation and
an explicit stale-explorer 404 browser scenario were not run for this increment.
The temporary verification server was stopped; the normal app remains open.
Stopped after this Welcome refinement.
