# First-time and returning Welcome states

Implemented the requested Welcome flow in the existing React application.
The purple hero/artwork and returning Adventure Trail design remain. Backend
services, XP rules, confirmation gates, database schema, LangGraph workflow and
other page layouts were not changed. Verification used only a separate synthetic
SQLite file; no records in the normal application's database were created/reset.

## Flow

1. With no selected Explorer response loaded from the backend, display
   **Welcome to CareerQuest AI**, **Your future is an adventure**, and only two
   setup fields: fictional nickname and grade 9–12. Create My Explorer performs
   the existing profile POST after explicit submission. No creation runs on mount.
2. The successful backend response identifies the saved explorer. A transient
   acknowledgement shows **Welcome aboard, {nickname}!** and a **First Mission:
   Discover Your Spark** card with one Start My First Quest CTA. The saved backend
   XP is shown; creation awards zero points and creates no XP event.
3. Start My First Quest opens the actual Quest 1. Leaving this acknowledgement
   clears it. Reloading also clears the transient acknowledgement, then restores
   the selected Explorer through the existing backend GET and shows Adventure Home.
4. Returning Home greets the saved nickname, derives its message and stages from
   persisted progress, and has one primary next-activity CTA in the highlighted
   Trail milestone. Completed/available stages and revisit links are retained.
5. Switch Explorer is available as a secondary Home header control in all states.

The locally remembered ID only selects which fictional Explorer to fetch; it does
not prove existence, completion, confirmation or XP. Those values come from the
API response. The creation acknowledgement is not a stored first-time-user flag
and cannot unlock personalized actions. This remains the existing browser-selected
fictional-profile demo, not a new authenticated student-account system.

## Files changed

- `frontend/src/App.jsx`: transient successful-creation acknowledgement, synchronous
  in-flight submission guard, welcome/first-mission transition, acknowledgement
  cleanup and heading focus. Both existing creation entry points acknowledge the
  real saved ID; the picker form layout and API calls are retained.
- `frontend/src/pages/Welcome.jsx`: explicit setup, aboard and returning views;
  two-field form, First Mission card, saved-name fallback and retained recovery UI.
- `frontend/src/welcomeMode.js`: new tested view selector using backend existence
  and quest progress plus the transient successful-POST receipt.
- `frontend/src/components/AppShell.jsx`: Home's secondary Switch Explorer remains
  visible before creation as well. Other pages' headers/navigation are unchanged.
- `frontend/src/pages/welcome.css`: scoped first-mission/setup presentation,
  readable text and responsive styling using the existing design.
- `frontend/tests/welcome-mode.test.js`: three view-selection/reload regressions.
- `frontend/tests/welcome-render.test.js`: new setup/aboard/reload/recovery/fallback
  render checks. The obsolete first-time expectation (creation submitted from the
  Trail) was replaced for this requested two-step flow; returning-state assertions
  and unrelated tests were preserved.
- `tests/test_welcome_flow.py`: isolated API contract covering creation at zero XP,
  repeated reads/reload, first-quest replay, confirmation and one persisted profile.
- This report, a reference from the prior report and `welcome-flow-*` evidence.

## Exact commands and final results

Executed from the project root:

```sh
.venv/bin/python -m unittest discover -s tests -v
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
```

**36 backend tests passed; 45 frontend tests passed; React production build
passed. Zero automated failures or skips.** No dependencies were added.
Existing allowlist, safe failures, persistence, confirmation and XP-integrity
checks remain passing. New/returning classification, missing nickname,
loading/error form suppression, the single returning Trail CTA and unchanged
other-page header controls are also covered by automated tests.

## Browser walkthrough and persistence evidence

Used localhost:18090 with a temporary SQLite database and one fictional Grade 10
explorer, **Nova Welcome Voyage**. A test-only wrapper outside application source
provided controllable read/creation delays, a synthetic read outage, a creation
request counter and exact-size viewport frames. It served the real compiled React
app and existing API; no production routes/services were modified.

- Delayed initial quest loading: the page displayed its loading state rather than
  prematurely showing a creation form. After loading, setup showed one text input,
  one grade selector and Create My Explorer, with no first-mission/Trail duplication.
- Filled nickname and grade. Held the creation response while checking the busy
  state: Create My Explorer was disabled. A repeated Enter attempt was refused by
  the disabled control. The server log recorded exactly **one** creation request.
- Released that response: the page displayed Welcome aboard and the requested
  First Mission card, with backend Grade 10 and **0 Explorer Points**.
- Opened the same origin in a fresh tab and reloaded it three times. Each restored
  the saved nickname and returning Home with one Trail CTA, no creation form and
  no transient aboard card. SQLite still contained **one Explorer**, **zero XP**,
  **zero events**, and the creation request counter was still **one**.
- Simulated an HTTP 503 on the selected-profile GET. An alert and Try again appeared;
  no creation form appeared during this unknown/error state. Cleared the outage
  and pressed Enter on Try again: the saved Explorer returned through reads only.
- In the original aboard view, Start My First Quest opened the actual Quest 1.
  Completed Quest 1, replayed its saved choice, and verified XP stayed at **20**.
- Returned/reloaded Home: its message said 1 of 3 completed; Continue Quest 2 in
  the Trail opened the actual second quest. Completed the remaining quests and
  explicitly confirmed the profile.
- Confirmed returning Home showed the saved nickname, **70 points**, completed
  Discover/Confirm stages, Explore recommended, and Plan/Reflect available.
  There were zero hero navigation controls and one prominent Trail CTA.
- Switch Explorer opened the existing explorer selection/creation page using Enter.
- Temporarily made only this isolated test nickname empty: reload displayed
  **Hi, explorer! 👋**, still with no creation form and one Trail CTA. Restored the
  fictional nickname afterward.
- Final SQLite/log checks still showed **one Explorer, one creation request, three
  quest completion events and 70 XP**. Creation/reload/retry awarded no points and
  created no duplicate Explorer. The normal application was reviewed read-only.

Duplicate prevention was verified for in-flight UI repeat submission and reload.
The existing backend creation protocol was preserved; no new network idempotency
protocol or automatic POST retry was introduced.

## Readability, accessibility and bounds

Real application frames measured exact 375px, 768px and 1280px widths for both
first-time setup and returning Home. Every document scroll width matched its
viewport. Titles measured 28px on mobile and 36px on larger screens; body text
measured 17px/18px respectively. No horizontal overflow was measured. First Mission
has responsive single-column CSS at narrow widths; its browser screenshot was
captured on desktop. Viewport overrides were reset after verification.

Fields retain explicit labels, validation and fictional-name guidance. Keyboard
submission, First Mission navigation, Trail continuation, switching and retry were
exercised. Loading/error roles and missing-name fallback were checked. Heading
focus handling is implemented for the successful creation acknowledgement. Full
screen-reader speech and native reduced-motion preference activation were not
exercised. No live model request was needed; retrieval remains curated/offline.

Evidence:

- [First-time Welcome](test-evidence/welcome-flow-first-visit.jpg)
- [Welcome aboard and First Mission](test-evidence/welcome-flow-aboard.jpg)
- [Returning confirmed Home](test-evidence/welcome-flow-returning-confirmed.jpg)
- [Read error and retry](test-evidence/welcome-flow-load-error.jpg)
- [Creation/reload counts and zero XP](test-evidence/welcome-flow-creation.json)
- [Final single-profile/XP counts](test-evidence/welcome-flow-final-counts.json)
- [Responsive measurements](test-evidence/welcome-flow-responsive.json)

The temporary verification server was stopped. The normal application remains
available at http://127.0.0.1:8000/. Stopped after verifying this Welcome flow.
