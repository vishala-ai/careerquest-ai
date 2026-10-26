# Adventure Home — implementation and verification

Historical report: this Dashboard / Adventure Home was subsequently replaced by
the simpler [Welcome page](WELCOME_PAGE_VERIFICATION.md) at the user's request.

Scope: Adventure Home only, in the existing React + FastAPI application.
Read `AGENTS.md` and all 17 sections of the locally retained UI/UX specification
in `docs/reference/UI_SPECIFICATION.txt`, including its original source metadata.
Inspected the current App, Dashboard, shared navigation/journey components,
Discovery Quests, profile state, API persistence contract, SQLite store and tests.
No backend service, schema, LangGraph workflow, Streamlit source or other page's
business behavior was changed. Existing database records were not reset or edited.

## Changes

- `frontend/src/pages/Dashboard.jsx`: Adventure Home greeting, neutral fallback,
  prominent XP/grade/quest summary, labeled native progress tracker, one Next
  Mission card, accessible Adventure Map, interest/roadmap summaries, topic
  previews, recent activity, and loading/error/retry states.
- `frontend/src/pages/adventure-home.css`: violet theme scoped to Home; 36px
  desktop / 28px mobile title; 18px desktop / 17px mobile body; supporting text
  at least 15px; responsive cards, visible focus and reduced-motion CSS. Shared
  header sizes change only while Home is visible. Other page styles are retained.
- `frontend/src/adventureHome.js`: tested, read-only domain projection of the
  backend profile response. Browser storage selects an explorer but does not
  supply XP, completion, confirmation, research or saved-roadmap status.
- `frontend/src/journey.js`: existing `dashboardNext` delegates to that same domain
  service. Other journey helpers retain their behavior.
- `frontend/src/App.jsx`: passes Home loading/error/retry and quest count; Home
  navigation focuses the destination heading. Other page functionality remains.
- `frontend/tests/adventure-home.test.js`: seven new domain regressions.
- `tests/test_adventure_home.py`: two new persistence/gate/legacy-name regressions.
- This report and `docs/test-evidence/adventure-home-*` screenshots/check results.

Next Mission routes:

| Persisted state | CTA | Actual destination |
| --- | --- | --- |
| No explorer | Create My Explorer | Existing explorer creation |
| Quests incomplete | Continue Quests | Existing Discovery Quests, first incomplete quest |
| Complete quests, initial unconfirmed profile | Review My Profile | Existing Explorer Profile |
| Confirmed, no saved exploration | Explore Career Worlds | Existing Career Worlds |
| Explored, no saved roadmap | Build My Roadmap | Existing My Roadmap |
| Saved roadmap | My Journey | Existing My Journey |
| Edited/unconfirmed profile, even with an old roadmap | Review Updated Profile | Existing Explorer Profile |

Historical exploration/roadmap completion remains visible after an edit, while
personalized map actions are locked until reconfirmation. A proposed roadmap
alone does not count as saved. Failed research does not count as exploration.
Revisits do not write XP. Quest continuation uses the server's saved sequential
quest count; the API already rejects out-of-order completions.

## Automated verification

Commands executed from the project root:

```sh
.venv/bin/python -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-baseline-pycache .venv/bin/python -m compileall -q careerquest app.py tests
PYTHONPATH=. .venv/bin/python scripts/smoke_core.py
```

From `frontend/`:

```sh
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm run build
```

The final CSS build was also run from the root:

```sh
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
```

Results: **35 Python tests passed; 14 frontend tests passed; zero test failures,
zero automated test skips.** Backend compilation, offline core smoke and React
production build passed. Existing test expectations were preserved. Tests cover
all mission transitions, missing/blank nickname, returning progress, unchanged XP,
failed research, proposal/save separation, draft confirmation gates and durable
SQLite records. No model call was used for this Home verification.

## Browser and actual API process checks

Used a separate localhost:18082 server and a newly created temporary SQLite
file; it did not use the existing application's database. The startup command
was the current absolute `.venv/bin/python` followed by:

```sh
-m uvicorn careerquest.api:app --host 127.0.0.1 --port 18082
```

A temporary verification-only wrapper outside the repository subsequently
served the same app and database, with a controllable `/api/quests` delay/outage.
It was launched with `-m uvicorn preview:app --app-dir <temporary-test-directory>
--host 127.0.0.1 --port 18082`. This wrapper never shipped in application source.
It enabled real loading/HTTP 503/retry checks without changing production routes.

Verified in Chrome:

1. New visitor sees the neutral greeting, zero saved progress, locked personalized
   steps, and Create My Explorer. Enter activates the creation destination.
2. Created fictional **Orbit Home Demo**, Grade 11, in the isolated database.
   Home displayed the backend nickname and 0 XP. Continue Quests opened Quest 1.
3. Saved Quest 1, returned Home and reloaded: 20 XP and Quest 2 remained. The CTA
   resumed the actual second quest. Completed all quests: 60 XP and Review My Profile.
4. Confirmed profile: 70 XP and Explore Career Worlds. The CTA reached the real
   Career Worlds page. Ran existing deterministic offline exploration, returned
   Home, and saw Build My Roadmap.
5. Created a roadmap proposal, explicitly confirmed/saved it, returned Home,
   and saw My Journey. That CTA reached the real My Journey page.
6. Revisited a completed quest from the map and replayed the same saved answer.
   XP stayed at 70. Reopened profile editing; Home showed Review Updated Profile,
   the earlier roadmap summary, and disabled personalized planning.
7. Stopped/restarted the isolated API process. The complete profile response
   before and after restart compared equal: 70 XP, three quests, successful
   exploration, saved roadmap version 1, confirmation history and unconfirmed draft.
8. Direct POSTs to exploration, roadmap proposal and roadmap save each returned
   HTTP 409 while the edited profile was unconfirmed. No model call ran.
9. Delayed the real quests request: Home displayed a `role=status` loading state
   and the main region had `aria-busy=true`. Released the delay and saved progress
   appeared. A controlled HTTP 503 produced `role=alert` and Retry loading progress.
   Clearing the outage and pressing Enter on Retry restored the saved Home.
10. Set only the isolated synthetic nickname fixture to empty, reloaded, and saw
    **Hi, explorer!** with the same 70 XP. Restored its fictional nickname afterward.
11. Keyboard Enter activated mission CTAs. After leaving Home, focus moved to
    the destination H1. Tab moved to a completed map step with a visible outline;
    disabled planning buttons could not activate. The accessibility tree exposed
    heading hierarchy, named progress with value/max, step status text, current
    step and locked controls. These are accessibility-tree/keyboard checks, not
    a claim that VoiceOver speech was tested.
12. Reconfirmed the unchanged draft: XP remained 70 and My Journey returned.
13. Opened the existing localhost:8000 application and verified the new Home reads
    its existing selected fictional explorer. No write action was performed there.
    The normal application is left open for review. Browser console error/warning
    readback was empty on successful final views.

Responsive evidence measured actual CSS viewport widths (Chrome's zoom required
adjusting the viewport override input; the values below are DOM-measured widths):

| Width | Document scroll width | Title | Body | Smallest supporting text checked |
| --- | --- | --- | --- | --- |
| 375px | 375px | 28px | 17px | 15px |
| 768px | 768px | 36px | 18px | 15px |
| 1280px | 1280px | 36px | 18px | 15px |

An initial check found the shared label rule shrinking the progress label to
13px. A Home-specific selector fixed it, and all three width checks were rerun.
No remaining horizontal overflow was measured. Viewport overrides were reset.
Six principal foreground/background color pairs were calculated at 5.76:1–7.17:1,
above the 4.5:1 normal-text threshold; this is not a complete accessibility audit.

Evidence:

- [Existing application Home](test-evidence/adventure-home-live.jpg)
- [Updated profile review state](test-evidence/adventure-home-desktop.jpg)
- [Saved roadmap / My Journey mission](test-evidence/adventure-home-saved-roadmap.jpg)
- [375px full page](test-evidence/adventure-home-375.jpg)
- [768px full page](test-evidence/adventure-home-768.jpg)
- [1280px full page](test-evidence/adventure-home-1280.jpg)
- [Loading](test-evidence/adventure-home-loading.jpg)
- [Controlled outage](test-evidence/adventure-home-error.jpg)
- [Measured responsive checks](test-evidence/adventure-home-responsive.json)
- [Restart and direct API gate checks](test-evidence/adventure-home-api.json)

## Gaps and boundaries

- VoiceOver/NVDA spoken output was not exercised; keyboard and accessibility-tree
  behavior were checked instead.
- Reduced-motion styles are implemented. The runtime preference was inactive;
  switching the OS preference and testing assistive technology remain manual checks.
- Research remains curated/offline. No live Groq request or live research was
  needed or claimed. LangGraph behavior and Streamlit fallback were preserved;
  the Streamlit UI was not launched during this page-only task.
- My Roadmap still has its existing five-item template. Other pages' pending
  specification work is unchanged and is not claimed complete here.
- Home's interest/status view reflects saved backend state. Unsaved fields on
  another page do not become Home progress; the existing unsaved-change guard remains.
- There are still no authenticated production student accounts. All new records
  used here are fictional and isolated from the existing database.

Stopped after Adventure Home implementation and verification.
