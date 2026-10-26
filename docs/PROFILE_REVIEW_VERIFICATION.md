# One Explorer Profile review and confirmation

Verified 2026-10-25, using fictional students only.

## Changes

Discovery Quests now keeps the three quests, saved Discovery Clues, concise story and validated Career World previews. It renders no proposed-profile panel, feedback radios, manual-profile editor or confirmation button. Its single prominent completion action is **Review My Explorer Profile**, which opens the dedicated page. Story generation/retrieval and retries do not confirm a profile, grant confirmation XP or call the Career Research Agent.

Explorer Profile now owns the complete review flow. Its primary heading is **Does This Feel Like You, {nickname}?**, with an Explorer fallback. Actual quest choices are separated from CareerQuest's suggested interpretation. Interests, preferred activities, exploration goal and corrections are visible together.

- **Yes:** one explicit **Confirm My Explorer Profile** action saves agreement, the confirmed profile version and the existing validated handoff.
- **Somewhat:** students keep agreed interests, add preferred interests and a required short correction, then generate a revision. Changes are displayed; the new proposal has no inherited Yes and is not confirmed.
- **Not really:** students can start from different interests or use the existing manual editor. Manual changes save an unconfirmed proposal, show interest/activity/goal differences, and return to review before confirmation.
- Confirmed returning students see a read-only saved profile, Edit Profile and one primary exploration action. Feedback and confirmation controls do not repeat.
- Editing a confirmed profile creates an unconfirmed version. Existing research/roadmap gates, prior profiles, handoffs and saved roadmaps remain intact.
- Bounded generation failures/limits leave a clearly labeled manual proposal that can still be explicitly reviewed. No fallback is presented as live AI output.

No model provider, credentials, Groq generation contract, Career World catalogue, Career Research Agent, LangGraph workflow or XP rules were replaced. Feedback continues to use the existing Discovery Agent service. Manual review choices and field changes are stored in existing draft event JSON; final review source/verdict is stored with the confirmation. Raw quest events remain unchanged. No database schema migration was required.

The confirmation contract accepts optional `review_verdict` and `review_story_id`. Different stale story references are rejected before writes; an exact replay of an already accepted confirmation remains idempotent. A new regression test initially reproduced HTTP 422 on that exact replay; the corrected service returns the existing result without extra XP, confirmations or handoffs. Legacy explicit-confirmation callers remain supported.

## Actual test results

| Check | Final result |
| --- | --- |
| Python suite | **111 passed, 0 failures, 0 skips**; existing 103 plus 8 new review-flow tests |
| Frontend suite | **85 passed, 0 failures, 0 skips**; includes 9 new page/review tests |
| React production build | Passed, Vite 5.4.21 |
| Backend compilation | Passed |
| Offline core smoke | Passed; zero model calls |
| Separate live Groq smoke | Passed with `openai/gpt-oss-120b`; no model responses mocked |
| Isolated process restart | Complete API state unchanged; exact confirmation retry unchanged |
| Normal API startup | Passed on localhost:8000; every existing database row unchanged |

Commands from the repository root:

```sh
.venv/bin/python -m unittest discover -s tests -q
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-profile-review-pycache .venv/bin/python -m compileall -q careerquest app.py tests scripts/smoke_discovery_handoff.py
PYTHONPATH=. .venv/bin/python scripts/smoke_core.py
.venv/bin/python scripts/smoke_discovery_handoff.py --live --output docs/test-evidence/profile-review-live.json
```

Backend tests use mocked Groq responses and real FastAPI, LangGraph and SQLite. The new tests cover new/returning reads, Yes receipt versus explicit confirmation, Somewhat and Not really revisions, agreed interests, correction persistence, untouched raw answers, stale-source rejection, validated handoff, exact retry integrity, preserved plans, reconfirmation gates and fresh-process persistence.

Existing frontend feedback assertions were moved to the new dedicated review component, rather than removed. The quest tests now assert their intentional absence there. New page tests cover the personalized heading/fallback, facts versus suggestions, one confirmation action, feedback branches, fresh review after revision, confirmed returning state, read-only quest agent activity and a bounded manual fallback. Existing backend expectations were not weakened.

The live smoke separately exercised real Groq generation and two model-selected LangGraph actions, followed by deterministic profile-review routing. It produced a 90-word story and valid `software`, `bioengineering` and `design` IDs, blocked unconfirmed personalization with HTTP 409, created handoff/profile version 1 at 70 XP, and replayed confirmation without extra writes. This was an API/provider smoke, not a live-AI browser feedback test.

## Browser walkthrough

An isolated localhost:18099 backend used temporary fictional SQLite storage and explicitly disabled live model credentials. The UI labeled its deterministic summaries. The test server and browser tab were closed afterward.

1. Created **Orbit Fictional**, Grade 11, at 0 XP. Completed all three quests, reaching 60 XP.
2. Verified the completed quest page had exactly one **Review My Explorer Profile** button, zero feedback radios and zero proposed-profile panels. Saved clues and Career World previews remained visible.
3. Opened the dedicated profile. Verified the nickname heading, separate actual choices and interpretation, interests, activities and goal.
4. Chose Somewhat, retained technology, added art and entered a fictional correction. Saw kept/added/removed interests; the profile stayed unconfirmed at 60 XP.
5. Chose Not really, preferred nature and generated another proposal. Earlier interests were set aside; original quest answers remained visible.
6. Reloaded and restarted the backend. The saved correction/proposal and 60 XP persisted.
7. Used the manual editor to choose art, Creative activities and Try a mini-project. Saved the correction. The new unconfirmed proposal showed interest, activity and goal changes. No confirmation button was available until a fresh Yes was selected.
8. Confirmed once using Enter. Reached 70 XP and handoff/profile version 1. Returning to the confirmed profile showed zero feedback radios and zero confirmation buttons.
9. Revisited quests: the single review CTA remained, without feedback controls. Opened Edit Profile: version 2 required confirmation and did not award XP.
10. After the existing bounded generation limit was reached, verified the clearly labeled manual proposal remained reviewable. Explicitly reconfirmed unchanged fields: profile/handoff version 2 was saved and XP remained **70**.
11. Restarted again with final code. The complete API state and an exact confirmation retry were unchanged: three quest completions, two intentional profile versions, two handoffs, five story versions and 70 XP.

Measured no horizontal overflow at **375px, 768px and 1279px CSS widths**. The last approximates the 1280px target because of existing browser zoom. Each tested review viewport had exactly one prominent confirmation action. Browser error-log readback was empty. Keyboard confirmation and semantic labels/headings were checked; no full screen-reader audit is claimed.

## Changed source files

- `careerquest/api.py`: optional review metadata, non-Yes confirmation rejection and stale draft-source handling.
- `careerquest/profiles.py`: persisted manual review/changes and confirmation source; exact accepted-review retry handling.
- `frontend/src/useDiscoveryGuide.js`: shared persisted Discovery Agent session loading/request hook.
- `frontend/src/components/DiscoveryGuide.jsx`: read-only story/preview presentation and shared history/provenance/change views.
- `frontend/src/components/ProfileDiscoveryReview.jsx`: dedicated feedback, guided revision, manual editing and explicit confirmation controller.
- `frontend/src/components/DiscoveryAgentPanel.jsx`: read-only preview mode and duplicate manual-action suppression.
- `frontend/src/pages/DiscoveryQuests.jsx`: removed embedded profile review controls; one completion CTA.
- `frontend/src/pages/ExplorerProfile.jsx`: personalized review page, actual-choice sidebar, reusable existing editor and confirmed read view.
- `frontend/src/App.jsx`: dedicated-page callbacks; removed obsolete quest-page review wiring.
- `frontend/src/spec.css`: scoped readable review typography.
- `tests/test_profile_review_flow.py`: eight new integration tests.
- `frontend/tests/profile-review-render.test.js`: nine new page/review tests.
- `frontend/tests/discovery-guide-render.test.js`: relocated existing feedback coverage; read-only preview assertions.
- `README.md`, this report and `docs/test-evidence/profile-review-*`: documentation and actual evidence.

## Evidence and unverified checks

- [Browser results](test-evidence/profile-review-browser.json)
- [Persisted API/history results](test-evidence/profile-review-api.json)
- [Restart and retry](test-evidence/profile-review-restart.json)
- [Normal database preservation and startup](test-evidence/profile-review-startup.json)
- [Live Groq smoke](test-evidence/profile-review-live.json)
- [Quest summary](test-evidence/profile-review-quests.jpg)
- [Single confirmation after revision](test-evidence/profile-review-before-confirm.jpg)
- [Confirmed returning profile](test-evidence/profile-review-confirmed.jpg)

No unresolved test failures or skipped automated tests. Live feedback revisions through the browser, a full assistive-technology audit and Streamlit UI startup were not performed. Career Research Agent behavior, other pages, saved database records, provider configuration and raw quest/XP history were preserved.
