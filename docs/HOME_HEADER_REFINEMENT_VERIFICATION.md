# Focused Adventure Home and shared-header refinement

Verified 2026-10-25 against the latest repository and the attached product request. AGENTS.md, the mounted header/Home components, styles, state selectors and existing navigation were inspected before editing. This increment changes Home/shared presentation only; it does not redesign Portfolio or add workflow features.

## Changes

- The shared header now mounts exactly one navigation menu: **Home · Discover · Explore Careers · My Portfolio**. The global Discover/Confirm/Explore/Celebrate strip is unmounted on every layout. Its old component remains unused; the full four-stage Adventure Trail appears on Home only.
- Only the actual primary destination is highlighted. Explorer Profile and the synthetic explorer switcher do not falsely highlight Home or Discover. Milestone/Portfolio subviews continue to use the existing My Portfolio navigation context. Profile access remains available through Home's Confirm milestone and the student menu.
- Home uses one persisted-record projection for its hero and trail. The roadmap/reflection message branches were removed. New, partial, unconfirmed, research-ready, research-in-progress, portfolio-ready, current-saved and changed-input states have distinct copy. Unknown/stale portfolio data never claims the current portfolio is ready.
- A current saved portfolio shows the saved nickname, the portfolio-ready greeting and change-direction message. All four stages are completed, with no Recommended Next/Previously completed labels. Celebrate says **Portfolio saved.** and contains **View My Portfolio** as the single dominant action. Other stages retain quieter revisit links. The returning hero has no navigation button.
- Historical portfolios remain distinct from current ones. After profile changes, Home requests reconfirmation and leaves completed research/history revisitable. The quiet Celebrate revisit goes directly to the existing saved Portfolio view, including its historical-version notice; it does not strand the student on the confirmation-gated milestone screen.
- The trail has stage-colored illustrated icon tiles, connected decorative SVG paths, white rounded cards and lavender/mint surroundings. Colors are violet `#6D28D9`, teal `#0F766E`, blue `#1D4ED8`, emerald `#065F46`, gold `#FBBF24` and dark text `#17213D`. Labels/actions remain real HTML. No CSS framework, dependency or raster asset was added.
- Home headings are 38px desktop/30px mobile, section headings 26–28px, milestone headings 20–22px, body text 18px/17px with 1.6 line height. Shared content maximum is 1160px. Header/Home controls have at least 48px minimum targets. Long nicknames wrap in the hero and abbreviate in the header with the full saved nickname in the accessible menu label.
- Header height is measured with ResizeObserver for focus/anchor offsets rather than fixed assumptions. The header stays sticky in normal-height viewports; in viewports at most 500px high it scrolls with the document so zoomed content is not obscured. The new observer does not invoke scrolling or reset the page on renders. Existing route/scroll logic in App.jsx is unchanged.

## Actual verification

| Check | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Full frontend suite | **175** | **0** | **0** |
| Full Python regression suite | **203** | **0** | **0** |
| React production build | Pass | 0 | 0 |

Sixteen new frontend tests cover the state matrix, current/historical distinction, one navigation/primary action, honest active-page styling, guarded current-portfolio claims, existing page targets, profile access, long nicknames, read-only rendering, typography, stage colors, minimum target sizes, reduced-motion/focus rules, dynamic header sizing and text contrast. White-on-stage buttons and dark-on-gold completion action meet the 4.5:1 normal-text threshold.

The first frontend run had **5 outdated presentation assertions**: the old global strip, Confirm-as-Discover highlighting, global current-step semantics, the former 1200px width and roadmap-based hero copy. Those assertions were updated to the explicitly requested UI behavior. No test was removed or skipped, and no XP, confirmation, snapshot or agent expectations were changed. The final counts above are passing results, not the initial run.

Commands from the repository root:

```sh
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
.venv/bin/python -m unittest discover -s tests -q
```

The isolated browser server used:

```sh
GROQ_API_KEY='' CAREERQUEST_DB=/private/tmp/careerquest-home-header-browser.sqlite3 CAREERQUEST_DEV_TOOLS=0 CAREERQUEST_CAREER_GROQ=0 .venv/bin/python -m uvicorn careerquest.api:app --host 127.0.0.1 --port 18111
```

Existing API calls supplied saved fictional fixtures between browser checks. The only explorer was created through the UI; fixtures explicitly completed quests, confirmed a profile, researched/shortlisted Software Development, saved a primary preference, explicitly confirmed one portfolio, then saved an unconfirmed profile draft. The test server was stopped with `kill -TERM 92539`. The normal backend was not restarted.

## Browser results

- **New explorer:** nickname/grade setup worked, account creation earned 0 XP, and reload resumed Start My First Quest without creating another explorer. The header had one menu and no strip.
- **Partial quests:** persisted Quest 1 produced 20 XP, “1 of 3” hero copy and Continue Quest 2. That action opened the actual second quest, with Discover as the only active primary item.
- **Unconfirmed:** three saved quests produced 60 XP and profile-review wording. The Home CTA opened the dedicated profile page, with no false Home/Discover primary highlight. Explorer Profile remained in the keyboard-operable student menu; Escape closed it and restored summary focus.
- **Confirmed/research:** explicit fixture confirmation produced 70 XP. Home offered career research, and Explore Careers opened the existing Career Worlds recommendations. After one research result, Home used in-progress exploration/shortlist wording. No full trail appeared on Career Worlds.
- **Portfolio-ready:** after explicit shortlist/preference saves, Home recommended the milestone. It opened the existing emerald screen with My Portfolio active, then the unchanged graphical preview with zero path dropdowns. These visits/refreshes left **70 XP and zero portfolio versions**.
- **Current saved portfolio:** an explicit fixture confirmation created version 1. Home then showed all four stages completed, no recommendation/history contradiction, one gold View My Portfolio action, and the portfolio-ready greeting. This was checked with a long saved nickname, not a hardcoded display name.
- **Changed profile:** after an unconfirmed draft, Home recommended Review Updated Profile and stopped calling the earlier portfolio current. Completed Discover/Explore/Celebrate remained unlocked. Revisit Celebrate opened saved version 1 with its historical notice. Review Updated Profile opened the editing/reconfirmation view. A direct personalized research request returned **HTTP 409**. Earlier snapshot interests remained `technology, art`, while the new draft had different interests. Navigation left **70 XP and one portfolio version**.
- **Responsive:** actual CSS widths **390px, 768px and 1440px** matched document width with no horizontal overflow. Mobile/tablet trail was vertical. Mobile main heading measured 30px, body 17px, primary target height 51.5px. Full nickname remained in the profile summary's accessible label while the visible header name abbreviated.
- **Sticky/focus:** header top remained 0 during ordinary desktop scrolling and after page changes. A focused Confirm node was fully below the header, with a visible solid outline. Opening/closing XP through an ordinary pointer click kept scrollY at **715 → 715**. Automated locator focus had moved the page to the header; the scroll check was repeated using a native pointer click to avoid confusing automation's focus behavior with a render reset.
- **200% zoom:** a dedicated `home-refinement.localhost` hostname isolated the test from the user's normal app zoom. Chrome's native toolbar reported **Zoom: 200%**. A 1440×1000 override became a 720×500 CSS viewport, with scroll width 720, readable text and a visible keyboard target at y=349–429 inside the 500px viewport. The short-viewport header scrolled normally instead of covering content. Zoom was restored to 100% on that test hostname; temporary viewport overrides were reset and both test tabs closed.
- **Back/Forward:** the existing document-level behavior was exercised. Back reached the prior test origin; Forward restored the in-progress Quest 2 document through browser cache with saved progress intact. App.jsx was unchanged. Internal page buttons still use the existing state-based routes and do not add separate browser-history entries; this increment does not introduce a router/history feature.
- **Motion/console:** loaded CSSOM contained the reduced-motion overrides; Home adds no visit-triggered celebration animation. No frontend JavaScript errors were recorded.

## Preservation and limits

All **22 protected backend/Portfolio/routing source files** matched their task-start hashes, including App.jsx, agent/provider code, Portfolio components, snapshot/PDF services and path-selection components. The normal SQLite schema and all table row/content fingerprints matched before and after verification. No secrets were inspected. No profile, shortlist, path, portfolio, PDF or XP implementation was changed. Generated frontend assets were rebuilt; refresh an already-open normal app tab to load them.

Actual OS reduced-motion activation, a full screen-reader audit and cross-browser testing were not performed. Reduced-motion CSS/semantics/focus checks and contrast tests passed, but are not a substitute for those audits. No live Groq inference was needed or tested for this presentation-only change.

## Changed files and diff

- `frontend/src/components/AppShell.jsx`: remove mounted global strip, retain one navigation and add measured focus offsets.
- `frontend/src/components/StudentTrail.jsx`, `student-trail.css`: brighter connected trail, distinct completed/current-history presentation and existing-page actions.
- `frontend/src/components/global-ui.css`: shared width/header/focus/target-size refinements and removal of unused strip styles.
- `frontend/src/pages/Welcome.jsx`, `welcome.css`: current projection/hero wiring and readable Home spacing/line height.
- `frontend/src/studentExperience.js`, `studentTrail.js`, `welcomeHero.js`: read-only progress/copy/presentation selectors.
- `frontend/tests/home-header-refinement.test.js` (new), `global-ui.test.js`, `welcome-hero.test.js`.
- Generated `frontend/dist/`, `README.md`, this report and `docs/test-evidence/home-header-*`.

There is no Git repository metadata in this workspace. The [readable unified diff](test-evidence/home-header-refinement.patch) contains the scoped implementation, test and README changes, excluding generated bundles, images and this report. It was prepared from pre-edit source copies and the recorded presentation-test edits.

[Browser/preservation evidence](test-evidence/home-header-browser.json) · [Completed desktop](test-evidence/home-header-completed-desktop.png) · [Completed mobile](test-evidence/home-header-completed-mobile.png) · [Portfolio-ready](test-evidence/home-header-ready-desktop.png) · [Needs-review/history](test-evidence/home-header-needs-review-desktop.png) · [200% zoom](test-evidence/home-header-200-percent.png).
