# Guided Career Worlds

## Current increment: emerald Career Discovery Milestone

Verified 2026-10-25. The referenced illustration was not attached/accessible in this request. The screen follows the described emerald/green, gold and white direction using a code-native decorative SVG adventure trail; it is not claimed to reproduce an unseen reference image.

### Implementation

- Career Worlds now offers a distinct emerald **Career Discovery Milestone** before its portfolio controls. The eligible heading uses the saved nickname: You did it, {nickname}! Its subtitle and FINAL STEP OF THIS ADVENTURE label follow the requested wording. White rounded progress cards, a gold CTA, mountains/compass trail illustration and a prominent change-direction reminder distinguish it from the purple Career Worlds interface.
- Progress comes from a read-only backend model. Researched careers are distinct stable IDs in persisted named-career exploration snapshots; shortlisted careers are distinct saved IDs across history, not research-run/re-save counts. Confirmed-interest count comes from the current confirmed profile. Stale/unconfirmed interests display an em dash instead of a fabricated number. The scope is explained beside the counts. Anonymous visitors have no invented zero counts or success claim; new fictional profiles have actual zero history and a prerequisite recovery action.
- `GET /api/profiles/{pid}/career-discovery-milestone` provides progress, confirmation context, eligibility, recovery target and whether completed portfolio history exists. Anonymous `GET /api/career-discovery-milestone` provides an honest setup state. These reads do not claim celebration receipts, award points or create portfolio/path versions.
- **Let's Create My Career Portfolio** calls `GET /api/profiles/{pid}/career-portfolio/entry`. The backend independently requires current explicit profile confirmation and at least one current, supported shortlist snapshot. Client progress flags cannot override it. Entry reads state only; path choices/completion still use their existing explicitly saved, validated endpoints. A profile change while the screen is open returns HTTP 409, refreshes progress and offers profile review.
- Entry opens the existing portfolio controls as a focused subview, with unassigned choices staying unassigned. The related portfolio view adds a read-only visual summary of actual confirmed interests, saved careers and explicit path preferences. The diagram is an exploration flow, not a career-fit inference. World browsing retains shortlist/history access; Explore More Careers and View My Career Shortlist return to their actual sections. Global navigation and other student pages remain unchanged.
- The milestone explains combining interests and careers, selecting a primary and optional secondary path, creating a visual map and explicitly saving a snapshot. Opening either screen does not save anything. Previous snapshots remain immutable; future explicit changes use the existing versioning.
- Returning completed-portfolio students see revision wording and skip the decorative star-arrival animation. No new reward/acknowledgement table or rule was added. Existing celebration receipt logic is suppressed while this transition screen is active; previously delivered first-time events are not recreated.
- Text remains large, native buttons support keyboard navigation, the heading receives focus after loading, and decorative art is hidden from assistive technology. Motion is a subtle finite star fade only under no-preference; reduced-motion disables animation/transitions. The screen includes loading, error/retry, anonymous, prerequisite, eligible, returning and stale states.

### Actual results

| Check | Result |
| --- | --- |
| Python tests | **182 passed**, 0 failures, 0 skips |
| Frontend tests | **130 passed**, 0 failures, 0 skips |
| React production build | Passed (Vite 5.4.21) |
| Backend compilation | Passed |
| Browser walkthrough | Passed for anonymous, eligible, returning, missing nickname, one/multiple shortlists and stale-profile entry |
| Normal backend startup | Healthy, LangGraph, port 8000; new endpoint works; developer access remains HTTP 403 |
| Database preservation | All row counts/content fingerprints and schema unchanged; no test students added to normal database |

Commands actually run:

```sh
.venv/bin/python -m unittest discover -s tests -q
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-milestone-pycache .venv/bin/python -m compileall -q careerquest app.py tests
```

Ten added backend tests cover anonymous/new students, confirmation/shortlist eligibility, distinct counts, entirely read-only view/entry/reload including celebration delivery flags and XP, missing nickname, stale context, completed-history preservation, ignored client eligibility flags and unknown IDs. Ten added frontend tests cover requested copy/counts, new/anonymous/no-success states, one/multiple counts, nickname/returning states, stale gates, keyboard-native semantics/loading/retry, read-only API wiring, reduced-motion/returning animation guards, contrast and a nonassigning visual map.

The first frontend run found one contrast failure for the warm-gold eyebrow on the brightest gradient sample. Its text color was lightened; the 4.5:1 minimum was retained, and the test now reads the actual stylesheet color. The final suite passes. No existing expected results or reward rules were changed.

### Browser details and limitations

Chrome used a temporary fictional SQLite database on loopback port 18105:

1. An anonymous visitor reached the screen with three em dashes, disabled creation and Create My Explorer recovery, without an earned-achievement heading.
2. River Fictional, Grade 11, was created through UI. Existing API fixtures supplied saved quests, explicit confirmation, two researched careers and one shortlisted career. Eligible screen counts were **2 / 1 / 2**, and the heading used the backend nickname.
3. Tab from the heading reached the primary CTA, then Explore More Careers, then View My Career Shortlist. Enter on the shortlist action focused its real heading. Returning to the milestone preserved the same counts.
4. Primary entry opened My Career Portfolio with both path selects empty and the visual map visible. Direct database verification showed **zero path versions and zero portfolio versions after viewing/entry**, with XP still 70.
5. A completed portfolio was then seeded explicitly through existing API save/complete operations to exercise returning behavior; it was not created by opening the screen. An isolated empty-nickname fixture produced You did it, Explorer!, returning revision wording and no star animation. A second explicit shortlist save updated the screen to **2 / 2 / 2**, preserving the one old completion version.
6. At actual **375px** CSS width, document width was 375px, heading 36px, body 17px, and primary button about 303px wide × 83px high. At **1279px**, document width matched the viewport and heading was about 56px. Returning star animation-name was none. Loaded CSSOM confirmed reduce-mode animation-name none and transition-property none; the actual OS preference was not toggled. Temporary viewport overrides were reset.
7. While an eligible screen remained open, an API fixture saved an unconfirmed profile draft. Pressing its still-visible primary CTA was rejected by the backend (409), then the screen refreshed to confirmation recovery, disabled creation, neutral heading and **2 / 2 / —**. There were no browser JavaScript errors. One automation locator used an unsupported heading-level filter and was corrected to the observed heading ID; that was not an application failure.
8. XP stayed **70** throughout. The completed portfolio history stayed at one version. Repeated viewing created no completion, path, reward or first-time milestone records. The test tab/server were closed/stopped after checks.

Normal backend handover had one transient verification probe reach the old process and return 404 for the new endpoint. The new listening process was verified and the probe then passed; no product workaround or extra database write was needed.

**Limits:** no illustration attachment was available, so matching an exact supplied image is unverified. Full screen-reader and actual OS-level reduced-motion tests were not performed. The global header retains its pre-existing missing-alias label; the milestone itself uses the neutral Explorer fallback. This transition is an internal Career Worlds subview, preserving existing navigation rather than adding URL routing; a full browser reload uses the application's existing Welcome entry, from which the screen can be revisited. No live Groq calls were added or tested for this deterministic presentation/read model.

### Changed files

- `careerquest/career_worlds.py`: read-only progress/eligibility model and portfolio-entry check.
- `careerquest/api.py`: anonymous/profile milestone and guarded read-only entry endpoints.
- `frontend/src/pages/CareerDiscoveryMilestone.jsx`, `career-discovery-milestone.css` (new): emerald screen, decorative SVG, states/actions/responsive/motion rules.
- `frontend/src/pages/CareerPossibilityMap.jsx` (new): actual saved-choice visual summary.
- `frontend/src/pages/CareerWorlds.jsx`, `career-worlds.css`: transition/portfolio subviews, context-aware navigation and map styling.
- `tests/test_career_discovery_milestone.py`, `frontend/tests/career-discovery-milestone.test.js` (new).
- Generated `frontend/dist/`, `README.md`, this report and evidence below.

Agent tools/workflows, Groq configuration, XP services, database schema/history, quest/profile services, Streamlit and unrelated student pages were preserved.

[Browser evidence](test-evidence/career-discovery-milestone-browser.json) · [Startup/data preservation](test-evidence/career-discovery-milestone-startup.json) · [Desktop screenshot](test-evidence/career-discovery-milestone-desktop.png) · [Mobile screenshot](test-evidence/career-discovery-milestone-mobile.png).

---

## Previous increment: personalized career celebrations

Verified 2026-10-25 with fictional students only.

### Inspection and implementation

Research snapshots, distinct shortlist selections and primary/secondary path versions were already persisted. Career actions had no XP or badge rule. The existing rewards are quest completion, explicit profile confirmation and reflection; those services/rules were not changed. There was **no persisted portfolio-completion state** to celebrate, only saved choices.

This increment adds six first-time milestones: first named career researched, first distinct career shortlisted, second distinct career shortlisted, first primary path, first optional secondary path and first explicitly completed Career Discovery Portfolio snapshot.

- Shortlist celebrations use the nickname loaded from the saved profile and the actual selected career title from its saved research snapshot. Missing nickname uses Explorer. Messages reinforce curiosity, multiple possibilities and changing direction. They do not infer ability, fit, diagnoses, admission chances or a permanent decision.
- Small, nonmodal success cards provide Explore Another Career, View My Shortlist, Choose My Paths or Review My Portfolio according to the milestone. Their actions acknowledge the receipt and focus the relevant heading. Dismissal is keyboard-accessible. Cards do not auto-dismiss or steal focus when they appear. The largest card is reserved for completion.
- `career_milestones` stores kind, actual source-record ID, confirmation event, nickname/career payload, timestamp, delivery and acknowledgement. Each kind is unique per explorer for their lifetime. Recording shares the authoritative research/save transaction, so a failed save cannot leave a celebration for an achievement that did not persist.
- Successful prior research and existing shortlist/path history prevent retroactive first-time celebrations. Re-saving a snapshot or researching/shortlisting the same career again does not create another milestone. Later third/further shortlist saves retain a concise personalized success notice rather than a new first-time celebration.
- The server atomically claims **one** unseen receipt at a time through `POST /api/profiles/{pid}/career-celebrations/claim`. `POST /api/profiles/{pid}/career-celebrations/{mid}/acknowledge` saves dismissal/action acknowledgement idempotently. Neither creates XP or badges. Reload/remount does not redeliver a claimed receipt. Pending receipts from an older profile confirmation are not shown as current.
- Portfolio now has an explicit **Review and complete your portfolio** action. It requires the current confirmed profile, current explicitly saved careers and saved paths. A secondary path stays optional. This records an immutable `career_portfolio_completions` version with confirmation/profile/path references, a source signature, chosen careers/paths and source metadata. A changed shortlist/path/profile makes the earlier completion historical; a new current snapshot requires another explicit review and completion. The first-time completion celebration is not replayed for later versions.
- Expected signatures reject stale completion submissions. Identical completion retries return the same version. Neither saving paths nor claiming, dismissing or completing a portfolio grants rewards or bypasses profile confirmation.
- Animation is one subtle 180ms arrival only under `prefers-reduced-motion: no-preference`. The reduce rule disables animation/transitions and smooth scrolling. Cards use polite, atomic status announcements, native buttons, readable text and a constrained scrollable height on mobile. No sounds, flashing or confetti were added.

### Actual checks

| Check | Result |
| --- | --- |
| Full Python suite | **172 passed**, 0 failures, 0 skips |
| Full frontend suite | **120 passed**, 0 failures, 0 skips |
| Production React build | Passed (Vite 5.4.21) |
| Backend compilation | Passed |
| Actual isolated server restart | Overview/completion unchanged; no celebration redelivered |
| Normal backend startup | Healthy, LangGraph, port 8000; developer access remains HTTP 403 |
| Normal database preservation | All pre-existing row counts/content fingerprints unchanged; two new empty tables |

Exact commands from the repository root:

```sh
.venv/bin/python -m unittest discover -s tests -q
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-celebrations-pycache .venv/bin/python -m compileall -q careerquest app.py tests
```

Seventeen new backend tests cover first/repeated/failed research; correct saved identity/career; distinct first/second selections; separate primary and optional secondary milestones; one-at-a-time delivery; explicit completion and no forced secondary; duplicate/revised completion; stale signatures; profile edits; owned/idempotent acknowledgement; returning history; process restart; rejected client reward fabrication; nickname fallback; and atomic rollback. Eight new frontend tests cover personalized/supportive copy, all six actions, accessible statuses/buttons, completion-only emphasis, escaping/fallback, reduced-motion CSS, explicit optional-secondary completion and persisted API integration. No existing expected test results were changed in this increment.

### Browser outcomes

Chrome used **Orion Fictional**, Grade 11, in a temporary database on loopback port 18104. Creation used UI; quest and explicit profile-confirmation prerequisites used the existing API. Groq was deliberately unavailable; celebrations use deterministic language, not model inference.

Observed all six cards:

1. Researching Software Development showed Curiosity in action, Orion Fictional with that actual career name.
2. Tab from the card's primary action reached Dismiss celebration; Enter acknowledged it. Keyboard Save then showed Way to go, Orion Fictional and You saved Software Development.
3. View My Shortlist focused the shortlist heading. Reload and repeated Software research produced no repeated cards.
4. Saving Digital Product Design showed More than one spark and encouraged exploring multiple possibilities. Choose My Paths focused its heading.
5. Saving Software primary with no secondary showed the primary milestone and stated that a second path is optional. Adding Design later showed the distinct secondary milestone.
6. Explicit completion showed the larger personalized completion card. Review My Portfolio acknowledged it. Reload kept the completed snapshot but showed no celebration.

All six receipts were delivered and acknowledged exactly once. Final state: two shortlisted careers, two path versions, one completed portfolio version and **70 XP before and after the career flow**. Quest/profile event history was unchanged by these operations. No browser JavaScript errors were observed. A real isolated server restart preserved the entire career-discovery response and returned no further celebration.

At actual 375px CSS width, the document was 375px wide. The normal card was about 343px × 435px; completion was about 343px × 503px within an 811px viewport. At 1279px, the completion card was 520px wide. Both mobile cards fit the viewport and did not overflow the document. Temporary viewport overrides were reset. Reduced-motion rules were read from the actual loaded CSSOM: the reduce rule had animation-name none and transition none. The OS preference was **not toggled**, so no emulated reduced-motion screenshot is claimed. Some mobile/completion screenshot captures were blank and discarded; retained images show the first-shortlist card and persisted completed state.

### Changed files

- `careerquest/career_milestones.py` (new): transactional milestone recording, one-time claim and owned acknowledgement.
- `careerquest/career_worlds.py`: milestone hooks and versioned explicit portfolio completion/read state.
- `careerquest/store.py`: additive milestone/completion tables.
- `careerquest/api.py`: validated completion, claim and acknowledgement endpoints.
- `frontend/src/pages/CareerCelebration.jsx`, `CareerPortfolioCompletion.jsx` (new reusable components).
- `frontend/src/pages/CareerWorlds.jsx`, `career-worlds.css`: personalized feedback, persisted delivery/actions, portfolio review/completion and motion/responsive styling.
- `tests/test_career_celebrations.py`, `frontend/tests/career-celebrations.test.js` (new).
- Generated `frontend/dist/`, `README.md`, this report and evidence below.

No other student page, XP reward service, quest answers, provider configuration or LangGraph workflow was rewritten. No real student data or secrets were read. The normal database contains no new test explorers and no retroactively created celebration/completion records. Temporary test tabs/server were closed/stopped.

**Limits:** delivery is intentionally at most once: if a tab closes between the server claim and visible paint, that card may be missed rather than replayed; its milestone receipt remains stored. No full assistive-technology audit or actual OS reduced-motion toggle was performed. Completion is an educational snapshot in the existing Career Worlds portfolio section, not a new export/certification or a permanent career choice. No live model test was needed or run for this deterministic feature.

[Browser/XP and restart evidence](test-evidence/career-celebrations-browser.json) · [Normal startup/preservation](test-evidence/career-celebrations-startup.json) · [Shortlist celebration screenshot](test-evidence/career-celebration-shortlist.png) · [Completed snapshot screenshot](test-evidence/career-portfolio-completed-state.png).

---

## Previous increment: recommendations first and exploration paths

Verified 2026-10-25. This section supersedes the student labels and two-career comparison limit in the historical increments below.

### Exact diagnosis, reported before implementation

The recommendations landing view was **already implemented**, with `detail` initialized to `null` in `CareerWorlds.jsx`. It did not automatically restore `state.last_research`, local storage or a database selection. Those older App-level result values were not passed into this page.

Two source paths explained the detail-first experience:

1. App navigation called `setPage('worlds')` even if already on that page. React retained the same `CareerWorlds` instance/key and its local `detail`. Clicking the active top tab therefore kept the previously opened detail.
2. The Career Worlds next-step controller used `explore(next.world_id)` for its first suggested world. That explicit button bypassed the recommendation list and opened one researched career immediately.

The running normal server's index was fetched before edits and exactly matched `frontend/dist/index.html` (JS `index-Dzi-Em5s.js`, CSS `index-CrC7xExF.css`). No outdated served build was found. This does not establish what an independently cached browser tab had loaded. The diagnosis was based on actual source/render conditions and the running server, not a claim that the missing screenshot or a specific old browser session was inspected.

The recommendation service already used deterministic tag matches against confirmed interests and an active, versioned Discovery handoff. It was not a new live Groq recommendation call. The service filtered to handoff candidate IDs, so a one-world handoff could suppress other supported interest matches. Career comparison was bounded to two catalogue IDs; there was no persisted primary/secondary path preference feature.

### Implemented behavior

- Every top-navigation entry to Career Worlds remounts only this page, including a click on the active tab. Default local state is recommendations, with no research request until an explicit career/comparison action. The next-step browse action now returns to recommendations instead of researching the first match.
- Recommended Careers for You shows up to three distinct, approved records with name, existing short catalogue description, visible **Why suggested?**, and **Explore Career**. Explanations and evidence IDs refer to the latest confirmed interests/confirmation. Current handoff IDs are preferred for inclusion, then other valid confirmed-interest matches can fill available slots. The immutable handoff is not rewritten. These are possibilities, not fit rankings.
- One, two or zero supported matches remain one, two or zero; exploratory/unsure profiles are not forced into recommendations. Explore All Careers exposes the remaining catalogue records; recommended records remain accessible above without duplicate cards. No new career records or claims were invented.
- Explore Career passes the stable existing world ID to the Career Research Agent through the existing graph. Details retain activities, skills, related educational fields, sources and optional demo missions. **Back to Recommended Careers** restores the landing and focuses its heading. Historical notes open only through explicit saved-detail controls.
- A visible Compare Careers section accepts two or three distinct supported careers. One bounded existing research action retrieves those IDs. A side-by-side table uses the actual cited facts, followed by existing full notes and per-career Save controls. On mobile its table scrolls inside a labeled, keyboard-focusable region, without overflowing the document. The optional AI question disclosure remains available and uses the existing Groq/policy configuration.
- Research and recommendations do not auto-save a shortlist. After explicit saves, the portfolio section offers **Primary Exploration Path** and optional **Secondary Exploration Path**. Both start unassigned. Students choose and save; the secondary cannot equal the primary. No career priorities, profile confirmations or XP are assigned by this feature.
- `POST /api/profiles/{pid}/career-paths` requires the current confirmed profile, distinct approved IDs, explicitly shortlisted current-profile snapshots and expected profile/path versions. Concurrent stale submissions return a conflict; identical saves are idempotent.
- New additive `career_path_preferences` records preserve each choice version, confirmation event, source profile version, timestamp, shortlist/exploration references and source metadata. Preferences are returned with current/history state by the existing career-discovery read model. Profile edits invalidate current recommendations/paths and label previous history stale. Old career notes, handoffs, path versions and roadmaps remain preserved. Fresh confirmation does not silently reuse old shortlist snapshots for new paths.
- The frontend uses the career-discovery response for recommendation confirmation/context, including when the parent profile state was stale. It clears an open detail when the backend confirmation context changes. Developer controls remain absent from student mode and protected server-side.

### Actual verification

| Check | Result |
| --- | --- |
| Python suite | **155 passed**, 0 failures, 0 skips |
| React/Node suite | **112 passed**, 0 failures, 0 skips |
| Frontend production build | Passed (Vite 5.4.21) |
| Backend compile | Passed |
| Offline core smoke | Passed; 0 model calls |
| Isolated actual backend process restart | Entire career-discovery response unchanged |
| Normal backend startup | Healthy, LangGraph engine, port 8000; developer access HTTP 403 |
| Normal DB preservation | Every pre-existing row count/content fingerprint unchanged; one new empty path table |

Exact verification commands from the repository root:

```sh
.venv/bin/python -m unittest discover -s tests -q
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-recommendations-pycache .venv/bin/python -m compileall -q careerquest app.py tests
PYTHONPATH=. .venv/bin/python scripts/smoke_core.py
```

Fourteen added backend tests cover three/one/two/no valid matches, no forced exploratory recommendations, handoff preservation, read-only landing, two/three-career tools and source references, invalid/duplicate/too-many IDs, explicit shortlist prerequisites, primary/optional-secondary paths, idempotence/version history, stale browser conflicts, profile-change invalidation, fresh-process persistence and another explorer's unsaved selections. Eight added frontend tests cover recommendation cards/reasons/empty states, visible comparison controls and cited table, unassigned/optional/stale path controls, history summaries and navigation reset wiring.

The first frontend run had two failures: reasons appeared on a non-recommended test card, and a recommendation badge could remain in an unconfirmed render. Rendering was fixed to require both current backend confirmation and recommendation state. The same assertions passed afterward; they were not loosened. Existing expected UI labels were updated for the requested Explore Career/Explore All Careers wording. No XP, persistence, allowlist or confirmation expectations were changed.

### Browser walkthrough

Chrome used **Lyra Fictional**, Grade 10, in a temporary SQLite database on loopback port 18103. Explorer creation used UI; saved quest and explicit confirmation prerequisites used the existing API, with live model credentials deliberately unavailable.

Verified in the actual UI:

1. Technology profile opens three distinct recommended cards and reasons before any detail; all four supported careers remain accessible.
2. Opening Software then clicking the already-active Career Worlds top tab returns to recommendations with zero detail panels. Returning from My Journey and reloading also shows recommendations, not an automatic saved detail.
3. Comparing Software, Design and Environment produces three table rows, three detailed worlds and 25 comparison citation links. Existing backend tests also verify two-career comparison.
4. Explicit keyboard/button saves produce exactly two shortlisted careers. Primary/secondary controls initially remain empty. Choosing Design primary and Software secondary creates one saved path version, preserved in form controls after reload.
5. Explicit Resume saved detail opens Design; Back restores recommendations. Revisits do not make research calls or award XP.
6. Actual measured CSS widths **375px**, **768px**, and **1279px** have matching document widths, with no horizontal page overflow. At 375px the title is 28px and body 17px. The comparison table is 720px wide inside a 296px scroll region. Desktop typography remains 36px/18px. Temporary viewport overrides were reset. The first measurements were 562px/1920px because of existing browser zoom; controls were adjusted and actual CSS widths measured rather than claiming those were 375/1280.
7. An unconfirmed nature-interest edit removes current recommendation cards and active paths, retains path history, and leaves four public career actions. Explicit reconfirmation shows exactly one Environmental Science recommendation. A confirmed unmatched interest shows zero recommendations, an honest explanation, and all four catalogue careers.
8. Student developer-control count: 0. Student browser JavaScript errors: none. Entire persisted career-discovery JSON survives a real isolated-server restart, including seven exploration snapshots, two shortlist selections and one now-stale path version.

XP stayed at 70 through research/comparison/saving/path selection. The existing profile-confirmation service then awarded its existing version rewards during the two explicit reconfirmation fixtures, producing 80 and 90 XP. This increment did not modify that service or award research/path XP. Tests separately verify repeated path saves do not create duplicate versions or change XP.

The normal backend was restarted with final code and developer tools disabled. No test explorers were added to its database. Only the empty additive table was created; all existing rows were fingerprint-checked. Temporary browser tabs and test server were closed/stopped.

**Limits:** recommendations/comparison are deterministic catalogue matching/retrieval, not live Groq-generated career advice or live verified web research. Existing Groq tests use mocks; no live inference was requested in this increment. There are four approved career records, so coverage beyond them is unavailable. A full assistive-technology audit was not run; keyboard saves, heading focus and semantic comparison labels were checked. Paths live in the existing Career Worlds portfolio section and backend read model; this does not introduce a separate portfolio page/export or automatically change roadmaps.

### Changed files

- `careerquest/api.py`: three-ID request bound and validated path-save endpoint.
- `careerquest/career_worlds.py`: supported recommendations/evidence/context, three-ID validation and versioned paths.
- `careerquest/store.py`: one additive path-history table.
- `frontend/src/App.jsx`: Career Worlds entry key only; other pages preserved.
- `frontend/src/pages/CareerWorlds.jsx`, `career-worlds.css`: recommendations-first landing, reset/back/compare/portfolio integration and responsive styling.
- `frontend/src/pages/CareerComparison.jsx`, `CareerPortfolioPaths.jsx` (new reusable components).
- `tests/test_career_recommendations_paths.py` (new).
- `frontend/tests/career-recommendations-paths.test.js` (new), `career-worlds.test.js` (requested wording assertions).
- `frontend/dist/` regenerated build, `README.md`, this report and evidence below.

Groq credentials/configuration, LangGraph tools/workflows, research implementation, catalogue facts, profile/quest services and Streamlit fallback were not rewritten.

[Browser results](test-evidence/career-recommendations-browser.json) · [Responsive measurements](test-evidence/career-recommendations-responsive.json) · [Normal startup/preservation](test-evidence/career-recommendations-startup.json) · [Recommendations screenshot](test-evidence/career-recommendations-desktop.png) · [Mobile screenshot](test-evidence/career-recommendations-mobile.png) · [Saved paths screenshot](test-evidence/career-exploration-paths.png).

---

## Previous increment: student/developer separation

Verified 2026-10-25. The earlier implementation record below is historical; the developer disclosure described there has now been removed from the student page.

### Changes

- Career Worlds no longer mounts developer controls, Groq toggles, failure switches or JSON receipts. Its requests do not send tester flags. Questions and comparisons remain available. Student provenance uses concise wording and still labels unavailable AI routing honestly.
- A server-derived next action follows persisted records: explore a world, revisit notes to choose a career, view the saved Career Discovery Portfolio, or review an unconfirmed profile. The portfolio action focuses the existing portfolio heading on this page. It does not invent a new portfolio route. A detail view's existing Save action is not duplicated by another save/revisit CTA.
- `/developer` is a separate React view, protected by FastAPI before serving its UI shell. `/api/developer/access`, `/api/developer/profiles/{pid}/research-receipts` and `/api/developer/profiles/{pid}/research` independently enforce the server boundary. There is no developer link in student navigation.
- Developer receipts project actual persisted run records into allowlisted fields: action, routing method, model identifier when recorded for a successful Groq decision, tool steps, outcome, error class, catalogue IDs and source validation. They exclude nicknames, interests, questions, quest responses, corrections, provider response bodies, API keys and model reasoning. Legacy receipts without model metadata are not assigned the current configured model.
- Explicit world selection remains deterministic. Free-text routing can be deterministic, Groq-directed or a labeled bounded fallback. The existing action contract, research tools and LangGraph structure remain intact. Core fallback routing now records its successful tool step as well as selection/failure steps.
- Failure simulation and explicit routing overrides are protected on the Career Worlds endpoints and the older `/explore` and `/reflect` surfaces, preventing an alternate API bypass. Existing test utilities remain available inside the permitted local environment or directly through Python domain functions.
- No database schema changes were needed. All pre-existing rows in the normal database had identical counts and content fingerprints across the final backend restart. Other student pages and their navigation were not edited.

### Local developer access and limitations

The application still has **no identity authentication**. This increment uses the requested local-environment alternative, not an authenticated developer role. Tools are disabled by default and require **all** of:

- `CAREERQUEST_ENV=local` and `CAREERQUEST_DEV_TOOLS=1` on the backend;
- a loopback `CAREERQUEST_HOST` and actual direct loopback socket peer;
- loopback Host and, when supplied, Origin; no Forwarded / X-Forwarded headers;
- no cross-site receipt/action fetches.

Top-level GET navigation to the UI shell is allowed in permitted local mode even when Chrome marks navigation cross-site. That exception does not authorize API data/actions or framing. The shell sends `X-Frame-Options: DENY`, `nosniff` and `Cache-Control: no-store`.

Only trusted local users should run this mode. It cannot distinguish two people using the same permitted local machine. **Do not enable it on shared/public deployments, reverse proxies or tunnels.** `.replit`'s `CAREERQUEST_HOST=0.0.0.0` fails the local boundary even if tools are accidentally flagged on. This does not add general application authentication or make the existing fictional prototype suitable for real student data.

For a separate, explicitly local developer process (choose an unused port):

```sh
CAREERQUEST_ENV=local CAREERQUEST_DEV_TOOLS=1 CAREERQUEST_HOST=127.0.0.1 \
  .venv/bin/python -m uvicorn careerquest.api:app --host 127.0.0.1 --port 8001 --no-proxy-headers
```

Open `http://127.0.0.1:8001/developer`. Use a fictional Explorer ID whose profile is explicitly confirmed. Controlled research saves ordinary run history; it cannot shortlist careers, confirm profiles, award XP or create roadmaps. Stop this separate process when testing is finished. The normal backend was left on port 8000 with developer tools explicitly disabled.

Student free-text routing defaults to the existing deterministic policy. A backend operator can set `CAREERQUEST_CAREER_GROQ=1` to use the existing configured Groq provider/model for these questions; no student toggle or new credentials are introduced. Explicit world selection/comparisons remain deterministic. Provider errors retain the bounded fallback.

### Actual checks

| Check | Result |
| --- | --- |
| Full Python suite | **141 passed**, 0 failures, 0 skips |
| Full React/Node suite | **104 passed**, 0 failures, 0 skips |
| Vite production build | Passed |
| Backend compilation | Passed |
| Offline core smoke | Passed; 0 model calls |
| Normal backend restart | Health OK, LangGraph engine; developer page/access both HTTP 403 |
| Normal database preservation | All existing row counts and content fingerprints unchanged; no schema changes |

Commands actually run from the repository root:

```sh
.venv/bin/python -m unittest discover -s tests -q
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-developer-pycache .venv/bin/python -m compileall -q careerquest app.py tests
PYTHONPATH=. .venv/bin/python scripts/smoke_core.py
```

Fourteen added backend tests cover default/shared/remote denial; Host, Origin, forwarding and cross-site checks; safe top-level navigation versus protected APIs; injected flags on new/legacy routes; actual sanitized receipts, including an interleaved-run regression that returns the requesting run rather than whichever run finished last; permitted failure simulation; recorded Groq model persistence; safe model errors; catalogue/confirmation gates; next-action transitions, reload, stale selections and idempotent saving; server-controlled student Groq policy; and legacy receipt provenance. Existing API test fixtures now explicitly opt into local tester mode for their existing simulation/routing cases; their expected outcomes were preserved.

Four frontend assertions/tests were added, and the former collapsed-debug-section assertion was replaced with the requested absence assertion. They cover no controls before authorization, routing/error/model receipt rendering, no student tester flags/raw receipts, and the one server-supplied next-step section.

Chrome walkthrough used **Aster Fictional**, Grade 11, in an isolated temporary SQLite database on loopback port 18102. Creation used UI; quest/confirmation prerequisites used the existing API. Checked:

1. Normal mode: four supported world actions, no developer controls, no checkboxes/raw receipts; direct `/developer` denied HTTP 403.
2. Career details still display citations; explicit keyboard Save creates one shortlist entry. The persisted next action changes to View My Career Discovery Portfolio and focuses its heading.
3. Reload plus isolated server restart preserves selection and 70 XP. Comparing Design and Software invokes both worlds and retains exactly one shortlist selection.
4. Explicit local mode: developer view loads actual saved deterministic trace, source metadata/evidence validation and tool status. Failure simulation returns a persisted blocked run / ConnectionError without new exploration or XP.
5. An intentionally unavailable Groq key exercises a clearly labeled bounded fallback / RuntimeError. It is not live model inference. Successful Groq routing/model recording was tested with a mock.
6. The student page remains free of debugging controls even when the test backend is in local developer mode. Final observed count: 0 developer controls, 1 portfolio next-action CTA, 3 explored snapshots, 1 shortlist entry, 70 XP. Student browser JavaScript errors: none.

The browser check found and fixed the top-level cross-site navigation issue described above. One automation locator failed because a `<summary>` was exposed differently by the native accessibility tree and Playwright; selecting its visible text worked. Final automated checks had no failures.

**Unverified:** live Groq inference, a full screen-reader audit, and effective mobile/tablet breakpoint measurements in this increment. A viewport override attempt did not change the measured 2880px browser width; it was reset, so no responsive pass is claimed. Existing responsive CSS was retained, with only scoped styling for the next-step card and separate developer page. The isolated test server and temporary tabs were stopped/closed; normal user tabs were preserved.

### Files changed in this increment

- `careerquest/developer.py` (new): local boundary and sanitized persisted receipts.
- `careerquest/api.py`: protected developer routes, legacy-control guards, server-controlled student routing.
- `careerquest/agent.py`, `careerquest/graph.py`: persist actual model identifier; core successful-tool receipt.
- `careerquest/career_worlds.py`: persisted-record next action.
- `frontend/src/pages/CareerWorlds.jsx`, `career-worlds.css`: clean student UI and next-step action.
- `frontend/src/pages/DeveloperResearch.jsx`, `developer-research.css` (new): separate tester view.
- `frontend/src/main.jsx`: select the separate developer entry surface.
- `frontend/dist/`: regenerated production build (index and bundled JS/CSS).
- `tests/test_developer_research.py` (new), `tests/test_api.py`, `tests/test_career_worlds.py`.
- `frontend/tests/developer-research.test.js` (new), `frontend/tests/career-worlds.test.js`.
- This report and `README.md`; evidence JSON and screenshots below.

[Browser outcomes](test-evidence/career-worlds-developer-separation.json) · [Normal startup/database preservation](test-evidence/career-worlds-developer-startup.json) · [Student screenshot](test-evidence/career-worlds-student-clean.png) · [Local developer screenshot](test-evidence/career-worlds-developer-local.png).

---

## Previous increment: initial guided Career Worlds implementation

Verified 2026-10-25 with fictional students only.

## Implemented experience

Career Worlds now begins with supported world cards, each with **Explore This World**. Up to three recommendations from the current confirmed interests appear first; remaining supported worlds follow without duplicates. Legacy confirmed profiles can use their confirmed interests without silently creating a new handoff. A saved exploratory/empty handoff does not force recommendations.

Selecting a world calls the existing Career Research Agent/LangGraph research tool with its validated stable catalogue ID. The detail view contains an overview, activities, skills, related educational fields, citations and an optional clearly labeled CareerQuest demo mission. World selection is deterministic student-directed routing, not an LLM choice. Source notes are curated offline, not live research or career-fit scores.

**Save to My Career Shortlist** is a separate explicit action. Exploration never automatically shortlists a recommendation. **Explore Another Career** returns to selection. The Career Discovery Portfolio on this page contains explored snapshots, explicit shortlist records and revisit controls. Revisit reads saved notes without running a new research request or awarding XP.

**Ask Your AI Career Guide** is optional and collapsed. Its question field starts empty. Students can ask free-text questions or compare two supported worlds. Optional Groq uses the existing provider/model to select a research action; curated explanations remain source-based. This page's research guard rejects reflection/plan actions, preventing accidental XP or plan writes from a career question. Technical settings, failure simulation and tool receipts are in a separate collapsed developer panel.

Confirmation is required server-side for new research, comparisons and shortlist saves. Unconfirmed students can browse public world descriptions and revisit their own historical notes. Profile edits invalidate current personalization; old explorations and selections remain in history, labeled as earlier-profile notes. A stale exploration cannot be newly selected under a changed profile until researched again.

## Sources and boundaries

The existing approved catalogue/IDs were preserved. New detail notes were curated separately against these primary sources:

- [O*NET Bioengineers and Biomedical Engineers](https://www.onetonline.org/link/summary/17-2031.00). The BLS biomedical overview returned HTTP 403 during preparation, so the detail explicitly cites O*NET; the original catalogue record was not rewritten.
- [BLS Software Developers, Quality Assurance Analysts, and Testers](https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm).
- [BLS Web Developers and Digital Designers](https://www.bls.gov/ooh/computer-and-information-technology/web-developers.htm). This is explicitly labeled related digital-interface work rather than a universal description of all product-design roles.
- [BLS Environmental Scientists and Specialists](https://www.bls.gov/ooh/life-physical-and-social-science/environmental-scientists-and-specialists.htm).

Fields are exploration topics, not school-specific admission requirements. Try-it missions are optional educational examples, not occupational facts. Every factual detail item has source IDs; missing/invalid source metadata blocks that detail instead of inventing content. Runtime metadata remains `live_verified: false`; these are not live-agent web results. No new model provider, credentials, SDK or live browsing tool was added to the application.

## Persistence

Two additive SQLite tables store `career_explorations` and `career_shortlist`. Snapshots retain stable world ID, source metadata, run ID, confirmation-event ID, profile version and timestamp. Selection ownership and current confirmation are validated on the server. Duplicate saves of the same exploration are idempotent.

Research runs and world snapshots commit atomically. A storage failure test rolls back both. A profile change during model routing prevents stale research from being persisted. Existing APIs, tool allowlist, default core/Streamlit behavior and original LangGraph routes remain available through default arguments; the bounded research-only mode is used by this page's new endpoints.

## Actual verification results

| Check | Result |
| --- | --- |
| Backend suite | **127 passed, 0 failures, 0 skips**; includes 16 new Career Worlds tests |
| Frontend suite | **100 passed, 0 failures, 0 skips**; includes 6 new Career Worlds render tests |
| React production build | Passed, Vite 5.4.21 |
| Backend compilation | Passed |
| Offline core smoke | Passed; zero model calls |
| Browser walkthrough | Passed using isolated fictional storage and explicit bounded fallback |
| Isolated API restart | Complete Career Discovery response unchanged, including portfolio/history |
| Normal API restart | Passed on localhost:8000; every pre-existing database row preserved |

Commands from the repository root:

```sh
.venv/bin/python -m unittest discover -s tests -q
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-worlds-pycache .venv/bin/python -m compileall -q careerquest app.py tests
PYTHONPATH=. .venv/bin/python scripts/smoke_core.py
```

Backend tests use real FastAPI, SQLite and installed LangGraph; Groq is mocked. Coverage includes all four stable-ID tool calls, valid source references, confirmed/legacy recommendations, explicit shortlist saving/replay, ownership checks, unsupported IDs, missing sources, simulated outage, Groq timeout, read-only action guarding, college routing, two-world comparison, changed-profile gates, concurrent-state rejection, fresh-process persistence, core fallback and atomic storage rollback. Existing expected results were preserved.

### Browser walkthrough

1. Created **Atlas Fictional**, Grade 11, in a temporary localhost:18101 database. Used existing APIs to complete prerequisite quests and confirm art/technology interests at 70 XP, keeping this walkthrough focused on Career Worlds.
2. Opened Career Worlds: three recommended cards first and Environmental Science afterward; four explicit world actions; optional guide/developer sections collapsed; no primary generic textarea.
3. Chose Digital Product Design. The research detail showed source-linked activities, skills, fields and an optional mission. The shortlist was still empty.
4. Pressed Enter on Save to My Career Shortlist. One selection appeared; XP stayed 70. The saved button became disabled.
5. Used Explore Another Career, opened the optional guide and compared Design/Software by stable IDs. Both detail views appeared. Portfolio exploration count became three; shortlist remained one.
6. Asked a college question, reaching the existing college research tool. Enabled optional Groq routing with the isolated server's credentials explicitly disabled; the next career question showed a clear bounded-fallback label and curated source notes.
7. Reloaded and revisited the explicitly saved Design notes. The portfolio persisted; no extra research or XP was created by revisit.
8. Opened an unconfirmed draft through the existing API. A browser with stale confirmed state tried another world and was blocked with HTTP 409. The UI refreshed its confirmation gate, removed personalized recommendations and retained all public worlds and saved history.
9. Restarted the isolated backend with the same database. The complete Career Discovery response matched exactly: three exploration snapshots, one shortlisted world and 70 XP. The isolated server and test tab were then closed.

Measured no horizontal overflow for both selection and detail views at **375px, 768px and 1279px CSS widths**. The last approximates 1280px due to existing browser zoom. Titles measured 28px mobile and 36px desktop. Keyboard save/revisit worked. Browser error-log readback was empty; HTTP 409 was deliberately verified as a successful gate check.

Live Groq inference, a full assistive-technology audit and Streamlit UI startup were not performed in this increment. The browser used deterministic/explicit fallback research; mocked Groq tests are not presented as live inference. Source pages are not re-fetched by the application.

## Changed files

- `frontend/src/pages/CareerWorlds.jsx`: new guided selection/detail, optional questions/comparison and portfolio UI.
- `frontend/src/pages/career-worlds.css`: scoped readable responsive page styles.
- `frontend/src/App.jsx`: replaces only the old Career Worlds rendering block with the page component.
- `careerquest/career_worlds.py`: approved-ID/source validation, confirmed-profile context, research detail assembly and portfolio persistence.
- `data/career_world_details.json`: separately curated cited details for the existing four worlds.
- `careerquest/agent.py`: optional stable-ID and research-only arguments; existing defaults retained.
- `careerquest/graph.py`: same optional context through the existing route/tool/finish graph.
- `careerquest/api.py`: Career Discovery, world exploration, safe guide, saved revisit and explicit shortlist endpoints.
- `careerquest/store.py`: additive tables and a noncommitting run primitive; public save behavior preserved.
- `tests/test_career_worlds.py`: sixteen new backend tests.
- `frontend/tests/career-worlds.test.js`: six new frontend tests.
- This report and `docs/test-evidence/career-worlds-*`.

No database reset or pre-existing record changes. Startup added the two empty tables to the normal database. Quest answers, profile versions/confirmation, XP, roadmaps, other React pages and provider configuration were preserved.

## Evidence

- [Browser results](test-evidence/career-worlds-browser.json)
- [Portfolio restart persistence](test-evidence/career-worlds-restart.json)
- [Normal database preservation and startup](test-evidence/career-worlds-startup.json)
- [Guided selection](test-evidence/career-worlds-selection.jpg)
- [Cited detail and explicit save](test-evidence/career-worlds-detail-saved.jpg)
