# Global UI refinement

Verified 2026-10-25 against the current repository and local specification. This increment changes React presentation and navigation only. Backend APIs, schemas, agents, Groq configuration, LangGraph, XP rules, Streamlit, and the normal SQLite database were not edited or reset. No credentials were read. The existing Explorer Profile component's source hash remained unchanged.

## Implementation

- Exactly four primary destinations: **Home, Discover, Explore Careers, My Portfolio**. Explore Careers uses the existing `worlds` destination and CareerWorlds component. My Portfolio uses that component's existing portfolio/milestone subviews; no duplicate career page or API was introduced.
- Explorer Profile is accessible from Confirm and the native student menu. Switch Explorer is secondary. My Roadmap and My Journey remain under Earlier saved activities, with their code and records preserved. The emerald milestone belongs to Celebrate, rather than a fifth primary tab.
- The persistent shared header shows the backend nickname, grade and XP. Missing identity uses Explorer; unavailable XP uses an em dash. An expandable explanation says points reflect saved activity, rather than ability or career fit.
- The four-stage indicator and Home's full trail use one tested, read-only projection of saved quest count, confirmation/version context, research, shortlist, paths and portfolio history. Historical completion remains accessible during reconfirmation. Profile Needs Review is persistent until explicit confirmation. Browser storage selects an explorer; it supplies no completion or reward flags.
- Shared components provide Navigation, StudentIdentity, XPBadge, StageProgress, PageHero/MissionInstruction and NextAction. Home alone retains the full illustrated trail. Discover/Profile/Explore/Celebrate accents are purple/teal/blue/emerald. The existing purple welcome hero, emerald milestone, graphical portfolio, research detail/comparison, explicit saves and version history remain.
- The final shared stylesheet loads after legacy styles. It establishes 1200px maximum content width, 36px desktop/28px mobile headings, 18px/17px body text, supporting text at least 15px in the inspected primary screens, focus indicators, native keyboard controls and reduced-motion rules. Mobile navigation exposes all four destinations without a hamburger menu. Verified small-text and explorer-switcher overflow defects were corrected.

## Commands and results

From the repository root:

```sh
.venv/bin/python -m unittest discover -s tests -q
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
```

| Check | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Full Python suite | 182 | 0 | 0 |
| Full frontend suite, including 16 new global UI tests | 146 | 0 | 0 |
| Production build | Pass | 0 | 0 |

The initial frontend run had three outdated presentation assertions: the former heading, former navigation structure and former source wiring. Those assertions were updated for the requested UI; reward, persistence and backend expectations were not weakened. Final suites pass. Browser checks found inherited 8px labels and a switcher overflow after text enlargement; both were repaired and rechecked. No dependencies were added.

The isolated browser server was started with:

```sh
GROQ_API_KEY='' CAREERQUEST_DB=/private/tmp/careerquest-global-ui-browser.sqlite3 CAREERQUEST_DEV_TOOLS=0 CAREERQUEST_CAREER_GROQ=0 .venv/bin/python -m uvicorn careerquest.api:app --host 127.0.0.1 --port 18107
```

The identified temporary process was stopped with `kill -TERM 89247`. The normal backend on port 8000 remained healthy and reported `langgraph`; it was not restarted.

## Actual browser walkthrough

1. Anonymous Home displayed the existing fictional nickname/grade setup, no invented identity or points, and exactly four primary links. Created **Juniper Fictional**, Grade 10, through the UI: 0 points and direct Start My First Quest navigation.
2. Saved Quest 1: 20 points and Continue Quest 2. Reload preserved nickname, grade, points and the first incomplete quest. Finished the remaining two quests: 60 points. Discovery Story used the explicitly labeled deterministic fallback because the isolated server had no Groq key.
3. Opened dedicated Explorer Profile review, chose Yes and explicitly confirmed: 70 points. The header marked Discover/Confirm complete and offered Explore. Research remained separate from story feedback.
4. Explore Careers opened recommendations. Explored Software Development through its existing stable ID and saved it explicitly. My Portfolio first opened the emerald milestone with actual counts **1 researched / 1 shortlisted / 2 confirmed interests**. Its primary action entered the existing graphical portfolio through the server gate.
5. Selected Software Development as the primary path; secondary stayed optional. Explicitly saved paths and completed the portfolio. Home showed four completed stages and one prominent View My Portfolio trail action. That action and the primary navigation reopened the saved portfolio. Points stayed 70.
6. Opened Explorer Profile from the student menu and used Edit Profile. The header displayed Profile Needs Review. Explore and Celebrate history stayed revisitable; Home recommended Review Updated Profile. A direct personalized research request returned **HTTP 409**. The saved portfolio version remained in history.
7. Reviewed and explicitly reconfirmed unchanged preferences: points stayed 70. Reload retained state. Re-researched/re-saved under the new confirmation and explicitly saved a second portfolio version. Final temporary database: **1 explorer, 3 saved quests, 70 points, 2 path versions and 2 portfolio versions**, with a current completed snapshot.
8. Exercised all four destinations, Confirm/Profile access and Switch Explorer. Enter activated navigation and native menus; Escape closed the profile menu and restored its summary focus. The XP explanation was keyboard accessible. Active page/stage semantics and labeled controls were visible in the accessibility tree. No JavaScript errors were recorded.
9. Measured **375px, 768px and 1279px** CSS viewports (1279px is the available approximately-1280px desktop setting at the browser's existing zoom). Document width matched the viewport. At 375px, Home, completed Discovery, Explorer Profile, Explore Careers, portfolio/milestone and the switcher had no final horizontal overflow. Headings measured 28px mobile and 36px desktop. Desktop main content measured 1200px. Mobile navigation targets exceeded 44px.

## Limits

- Exact 1280px was not measured; the desktop check used 1279px. A full screen-reader audit, actual OS-level reduced-motion activation and cross-browser testing were not performed. Loaded CSSOM confirmed the reduce-mode animation/transition/scroll rules.
- No live Groq inference was run for this UI change. Existing mocked/provider/error/agent tests passed. No live research or new AI capability is claimed.
- Final expanded screenshot capture was interrupted by the browser automation connection after earlier screenshots were saved. Subsequent viewport-reset/tab-close calls could not reconnect; successful cleanup of that browser override/tab is unverified. The temporary backend was stopped. Earlier functional checks and screenshots remain valid.
- The final explicit font-size overrides for legacy quest feedback/profile-status text passed the frontend suite and production build; those two styling overrides were not rechecked in the interrupted browser session.
- Navigation continues to use the existing application state destinations, rather than new URL routes. A full reload returns to Home with the saved explorer; the saved portfolio remains reachable from My Portfolio.

## Changed files

Existing files:

- `frontend/src/App.jsx`, `frontend/src/main.jsx`
- `frontend/src/components/AppShell.jsx`, `Shared.jsx`, `StudentTrail.jsx`
- `frontend/src/pages/Welcome.jsx`, `DiscoveryQuests.jsx`, `CareerWorlds.jsx`
- `frontend/src/studentTrail.js`
- `frontend/tests/career-worlds.test.js`, `career-recommendations-paths.test.js`, `welcome-render.test.js`
- Generated `frontend/dist/`, `README.md`

Added:

- `frontend/src/studentExperience.js`
- `frontend/src/components/Navigation.jsx`, `StudentIdentity.jsx`, `XPBadge.jsx`, `StageProgress.jsx`, `PageHero.jsx` (includes MissionInstruction), `NextAction.jsx`, `global-ui.css`
- `frontend/tests/global-ui.test.js`
- This report and `docs/test-evidence/global-ui-*` evidence.

[Browser results](test-evidence/global-ui-browser.json) · [Home desktop](test-evidence/global-ui-home-desktop.png) · [Home mobile](test-evidence/global-ui-home-mobile.png) · [Milestone](test-evidence/global-ui-milestone-desktop.png) · [Portfolio](test-evidence/global-ui-portfolio-desktop.png).
