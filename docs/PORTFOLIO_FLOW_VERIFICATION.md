# Career Worlds → Portfolio: final selection-and-confirm flow

Verified 2026-10-25 using fictional students and isolated test databases. The normal database was not reset, migrated or populated with test students. Its schema and every table's row count/content fingerprint matched before and after backend reload. Existing Groq configuration, Discovery Agent, Career Research Agent, LangGraph workflows, raw quest responses, confirmation gates and reward rules were preserved.

## Diagnosis and implementation

Previously, path selection was mounted inside Portfolio. The backend required a primary path, and completed snapshots stored only path/career references and sources. Those records could not supply a full historical Explorer Snapshot or version-specific graphical PDF without consulting mutable current data.

- **Explore Careers owns choices.** Research, comparison and explicit shortlist saves stay there. Its path controls offer a primary path, optional secondary path, or an explicit **I’m Still Exploring** selection. Only currently researched-and-shortlisted careers are offered/accepted. Optional student reasons are bounded to 240 characters and saved against supported shortlisted IDs. No priority is assigned automatically.
- **Preferences are versioned separately.** Existing `career_path_preferences.content` JSON now also supports `undecided` and `student_reasons`. No schema migration or existing-row update was necessary. Stale profile/selected-research references require updated preferences. Adding another saved career creates a new portfolio preview without requiring an unchanged primary path to be chosen again.
- **Milestone celebrates saved selections.** The emerald screen shows saved priorities or the undecided preference, and **Create My Career Portfolio**. Both entry and preview require a current confirmed profile, a current saved researched career and explicitly saved preferences. A second career is never required.
- **Portfolio is review-only.** The preview assembles an Explorer Snapshot, confirmed general interests, saved Discovery Story or labeled deterministic summary, branching adventure map, careers, cited skills, optional mission, actual student reasons and sources. It has no path dropdowns, reason fields or Save Exploration Paths control. Its primary action is **Confirm & Save My Portfolio**.
- **Confirmation freezes the server snapshot.** New format-2 versions include the actual profile, story provenance, career research details, selections, preferences, evidence references and sources. An optimistic signature binds the confirmation event, path preference version and exact shortlist selection IDs. Changed profile, path/reason or career-selection context rejects an outdated confirmation with HTTP 409. Identical retries are idempotent. Format-1 snapshots remain unchanged and are labeled honestly when they lack full historical profile details.
- **Saved portfolios stay immutable.** Download PDF uses the selected saved version ID, including historical versions. Create Updated Version opens the current preview; unchanged choices are already saved and cannot create duplicates. Interest changes route to Explorer Profile, and career/priority changes route to Explore Careers. Earlier portfolios remain accessible. PDF output reads only the selected immutable snapshot, with no live inference/research or current-profile substitution.
- **Existing celebrations are preserved.** Portfolio requests only its one-time completion receipt after saving, displayed inline with a secondary review action. Preview and the transient navigation/loading state claim nothing. Other queued exploration receipts remain for Explore Careers. No reward rule or XP award was added. Undecided completion wording says saved possibilities rather than claiming a priority was chosen.
- PDF output uses ReportLab with bundled Noto Sans fonts and license. Font origin/hash metadata is in `careerquest/assets/fonts/SOURCES.json`; the upstream [font directory](https://github.com/notofonts/noto-fonts/tree/main/hinted/ttf/NotoSans) and [license](https://github.com/notofonts/noto-fonts/blob/main/LICENSE) were checked. The Replit source allowlist includes these required assets and the curated career-detail catalogue, without broadening access to runtime data or credentials.

## Actual results

| Check | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Full backend suite | **203** | **0** | **0** |
| Full frontend suite | **159** | **0** | **0** |
| Production build | Pass | 0 | 0 |
| Backend compilation | Pass | 0 | 0 |

The 21 new backend tests exercise one/two/undecided preferences, prerequisite gates, bounded student reasons, immutable server-side snapshots, duplicate confirmation/XP prevention, stale profile/selection/reason signatures, fresh-process persistence, owned historical PDFs, source/catalogue outage behavior, literal markup safety, Unicode name preservation, Replit assets and scoped celebration delivery. Thirteen new frontend tests cover preview/saved/historical/legacy states, no duplicate path controls, source links, two/undecided branches, upstream edit links, readable responsive rules, Home routing and receipt guards.

Existing milestone/developer-routing fixtures were updated to explicitly save preferences before expecting portfolio eligibility, as required by this product decision. Their data-preservation, gate and reward assertions remain. Two milestone CTA assertions now use Create My Career Portfolio. The packaging symlink test creates its already-present fixture directory with `exist_ok=True`; its security assertion is unchanged.

Initial verification exposed four old eligibility/routing failures and one missing eligibility field error under the new prerequisite. Three newly written UI assertions needed HTML/attribute matching corrections. A Unicode PDF test detected inadequate font coverage, and an existing packaging fixture initially failed because explicit font assets now create its parent directory. These were corrected; final results above contain no failures or skips. Browser verification also caught and fixed celebration delivery during the unresolved entry screen. PDF visual review caught and fixed an orphaned source heading.

## Commands actually run

From the repository root:

```sh
.venv/bin/python -m unittest discover -s tests -q
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-portfolio-pycache .venv/bin/python -m compileall -q careerquest app.py tests
uv pip install --python .venv/bin/python 'reportlab>=4.2,<5' 'pypdf>=5,<7' 'pymupdf>=1.24,<2'
```

The initial `.venv/bin/python -m pip install ...` attempt failed because this virtual environment has no pip module. The available `uv` installer succeeded. Installed versions: ReportLab 4.5.1, pypdf 6.21.2, PyMuPDF 1.28.2. ReportLab and pypdf are declared in `requirements-api.txt`; PyMuPDF was used for local PDF rendering verification only. A temporary two-page PDF was parsed and both pages rendered/visually inspected after the final font/layout changes; that temporary PDF was removed.

Browser server, restarted with the same isolated database for persistence checks:

```sh
GROQ_API_KEY='' CAREERQUEST_DB=/private/tmp/careerquest-portfolio-flow-browser.sqlite3 CAREERQUEST_DEV_TOOLS=0 CAREERQUEST_CAREER_GROQ=0 .venv/bin/python -m uvicorn careerquest.api:app --host 127.0.0.1 --port 18109
```

The final normal backend was reloaded using:

```sh
.venv/bin/python -m uvicorn careerquest.api:app --host 127.0.0.1 --port 8000 --env-file .env --no-proxy-headers
```

The environment file was loaded by Uvicorn without displaying or inspecting credentials. The normal backend remains running and healthy with `agent_engine: langgraph`; new PDF and scoped-receipt APIs are present, developer access returns HTTP 403, and database fingerprints are unchanged. The final isolated server was stopped with `kill -TERM 91423`. Temporary browser viewport overrides were reset and the test tab closed.

## Browser walkthrough

- Created **Cedar Fictional**, Grade 10, through the UI. Existing APIs supplied synthetic saved quest answers and explicit profile confirmation as prerequisites; those discovery steps were not repeated as browser claims. Research, shortlist, preferences, milestone, portfolio preview/confirmation, upstream navigation and version-history actions were exercised in the browser.
- Researched and explicitly saved Software Development. Chose it as the primary path and added “I want to try building a tiny fictional game.” on Explore Careers. Milestone displayed **1 researched / 1 shortlisted / 2 interests** and that saved primary path. Portfolio had **0 selects and 0 textareas**. Enter confirmed version 1. Its PDF link used version 1's actual ID and was downloaded through the UI.
- Reload reopened saved version 1 with Download PDF/Create Updated Version. Added Digital Product Design and saved it as the secondary path on Explore Careers. My Portfolio automatically opened a new two-path preview, leaving version 1 unchanged. Explicit confirmation saved version 2.
- Chose I’m Still Exploring on Explore Careers. Both path selectors disappeared there, and the saved milestone/preview showed no assigned priority. Explicit confirmation saved version 3. A server restart and reload retained **3 portfolio versions, 3 preference versions and 70 XP**. Create Updated Version with unchanged current choices showed a preview with save disabled and upstream change links, preventing duplicate snapshots.
- Used fresh fictional explorers to test queued celebration integration. The first pass found the transient-entry issue; after correction, **Willow Fictional** entered a one-career undecided preview with zero celebrations/zero selects. Saving showed only `portfolio_completed`. First-research/shortlist receipts remained pending. Reload showed zero repeated celebrations, the same saved version and 70 XP.
- Tested **375px, 768px and 1279px** CSS widths. Document width matched each viewport, branches stacked vertically on mobile/tablet, mobile headings measured 28px, supporting text 15px, and confirmation target height exceeded 44px. Keyboard radio arrows, clickable labels and Enter confirmation worked. A prior floating Explore celebration initially covered an automation target; dismissing it resolved that interaction. The new saved-portfolio celebration is inline. No browser JavaScript errors were recorded.
- The saved version-2 PDF retained its original profile, two careers, priorities, student reason, skills, source URLs and optional mission despite later preference/profile changes in automated tests. Both final rendered pages were inspected with no clipped/overlapping text or orphaned heading.

## Changed files

- `careerquest/career_worlds.py`: versioned undecided preferences/reasons, stale selection checks, preview/snapshot assembly and historical-version lookup.
- `careerquest/api.py`: validated preference input, guarded preview and version/PDF endpoints, completion-only receipt query.
- `careerquest/career_milestones.py`: optional validated completion-receipt scope, retaining atomic once-only delivery.
- `careerquest/portfolio_pdf.py` (new), `careerquest/assets/fonts/` (new): offline saved-version PDF and licensed embedded fonts.
- `requirements-api.txt`: PDF runtime/parser dependencies.
- `frontend/src/pages/CareerPortfolio.jsx`, `career-portfolio.css` (new): visual review-only preview, immutable saved view, PDF/history/upstream actions.
- `frontend/src/pages/CareerPortfolioPaths.jsx`, `CareerWorlds.jsx`, `CareerDiscoveryMilestone.jsx`, `CareerCelebration.jsx`: Explore-only preferences, saved-selection handoff, isolated portfolio subview and undecided-friendly celebration copy.
- `frontend/src/studentExperience.js`: recommend preference selection before Celebrate when required by persisted state.
- `scripts/package_replit.py`: explicitly include required fonts/license and curated detail data.
- `tests/test_portfolio_flow.py` (new), `test_career_discovery_milestone.py`, `test_developer_research.py`, `test_replit_package.py`.
- `frontend/tests/portfolio-flow.test.js` (new), `career-discovery-milestone.test.js`.
- Generated `frontend/dist/`, `README.md`, this report and `docs/test-evidence/portfolio-flow-*`.

## Remaining limitations

No live Groq inference or live source research was run for this flow. Existing provider/agent tests passed; summaries are labeled according to their saved provenance. No full screen-reader audit, actual OS-level reduced-motion activation or cross-browser test was performed. Desktop verification measured 1279px rather than exact 1280px at existing zoom. Unicode text preservation was tested with a Greek-character nickname; CJK/emoji font coverage is unverified. PDF content matches the saved snapshot but uses a print layout rather than pixel-identical browser styling. Legacy portfolios cannot recover profile/story details that were never captured; they export only their original saved content with an honest explanation. Replit source packaging was tested, but no remote Replit deployment was performed.

[Browser results](test-evidence/portfolio-flow-browser.json) · [Startup/data preservation](test-evidence/portfolio-flow-startup.json) · [Two-path graphical portfolio](test-evidence/portfolio-flow-two-paths-desktop.png) · [Mobile](test-evidence/portfolio-flow-mobile.png) · [Saved portfolio](test-evidence/portfolio-flow-saved-desktop.png) · [PDF page 1](test-evidence/portfolio-flow-pdf-page-1.png) · [PDF page 2](test-evidence/portfolio-flow-pdf-page-2.png).
