# Student Discovery outcome and confirmed handoff

Implemented and verified on 2026-10-25 with fictional students only.

The existing Discovery Agent uses Groq (`openai/gpt-oss-120b` by the existing configuration) to select bounded tools inside LangGraph. That architecture is preserved. Story wording, evidence validation, catalogue matching, confirmation policy and handoff creation remain controlled Python logic. Sources are curated offline material, not live verified research.

## Behavior

- After all three saved quests, the agent response includes `outcome`: a concise Discovery Story, editable proposed Explorer Profile, up to three approved Career World suggestions with evidence references, and one optional mission. Partial explorers receive no final outcome.
- The quest page displays the proposed profile and opens the existing editable review form. Yes saves agreement and opens review. Somewhat and Not really retain their separate feedback/correction and revision flows. None confirms a profile.
- Explicit confirmation atomically saves the confirmation event, existing XP reward and immutable `discovery_handoffs` row. A failed handoff write rolls back confirmation and XP. Duplicate and concurrent confirmation requests do not create extra rewards or handoffs.
- Each handoff contains its ID/version, student ID, confirmed profile version/event, selected interests, validated suggested world IDs/reasons, evidence references, timestamp, and available story/mission/agent-session references.
- Suggestions are revalidated against the interests actually confirmed. Unknown or unsupported caller-selected IDs are rejected before writes. Invalid stored model candidates cannot cross the confirmation boundary.
- Corrections and feedback remain separate from untouched raw quest responses. Evidence includes exact quest event IDs and explicit confirmed-interest/correction/feedback references.
- Profile or quest edits make the old handoff inactive. Earlier profiles, handoffs, stories and roadmaps remain in history. Personalized research and new plans stay gated until explicit reconfirmation.
- Unsure students can confirm an exploratory profile with no career selection. Unsupported custom interests are retained without inventing matches.
- The Career Worlds page separates accepted suggestions from the complete catalogue. All four approved worlds, their existing descriptions and source metadata remain browseable before or after confirmation.
- A story/mission from different interests, corrections or uncertainty preferences is not promoted when confirming manual edits. Its source story ID/history remains available; a fresh narrative requires the Discovery Agent flow. Direct profile confirmation without generating a guide can therefore create a handoff without a story.
- Reads never silently backfill legacy profiles. Explicitly confirming an unchanged legacy profile creates its missing handoff without extra XP.

## Actual results

| Check | Result |
| --- | --- |
| Backend suite | **103 passed, 0 failures, 0 skips**: existing 84 regression tests plus 19 new handoff tests |
| Frontend suite | **76 passed, 0 failures, 0 skips**: includes five new render tests |
| React production build | Passed, Vite 5.4.21 |
| Backend compilation | Passed |
| Offline core smoke | Passed, zero model calls |
| Explicit live Groq smoke | Passed, no model responses mocked, real LangGraph |
| Normal API startup | Passed on localhost:8000; every pre-existing table's rows matched before/after startup and a profile read |
| Isolated backend process restart | Passed; complete API state identical, including two handoff versions, two story versions, two feedback records and XP |

Commands run from the repository root:

```sh
.venv/bin/python -m unittest discover -s tests -q
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-handoff-pycache .venv/bin/python -m compileall -q careerquest app.py tests scripts/smoke_discovery_handoff.py
PYTHONPATH=. .venv/bin/python scripts/smoke_core.py
.venv/bin/python scripts/smoke_discovery_handoff.py --live --output docs/test-evidence/discovery-handoff-live.json
```

Backend tests mock Groq responses while exercising real FastAPI, SQLite and LangGraph. Coverage includes handoff completeness, confirmation gates, malformed/invalid model output regression tests, invalid and unsupported world IDs, all feedback branches, separate raw answers/corrections, manual changes, uncertainty, version/history preservation, concurrent retries, transaction rollback, XP integrity and fresh-process persistence. Existing expected test results were not changed.

The separate live smoke used a temporary fictional database. Groq selected `revise_discovery_story` and `suggest_career_worlds`; bounded policy selected `request_profile_review`. The story was 90 words, generation status was `groq`, and no fallback was used. Handoff version 1 contained `bioengineering`, `software` and `design`. Unconfirmed personalization returned HTTP 409; explicit confirmation saved profile version 1 at 70 XP; repeat confirmation added nothing.

## Browser walkthrough

The isolated localhost:18098 backend used temporary fictional storage and explicitly disabled live model credentials. Its UI correctly labeled deterministic fallback output.

1. Created **Lumen Fictional**, Grade 10, at 0 XP. Completed three quests and reached 60 XP. Saw the summary, evidence-grounded worlds, optional mission and editable proposed profile.
2. Chose Not really, selected art and saved a fictional correction. The second story/proposal used art. Original quest choices stayed visible and XP stayed at 60.
3. Chose Yes. The form still required explicit profile confirmation and retained the correction. All four public worlds could already be browsed while personalization stayed gated.
4. Explicitly confirmed profile version 1. Handoff version 1 suggested Digital Product Design from art, at 70 XP. Expanded the saved handoff using Enter.
5. Opened Edit Profile. Personalized suggestions disappeared, all catalogue worlds stayed visible, and reload preserved reconfirmation and 70 XP.
6. Confirmed version 2 as unsure with no interests. Handoff version 2 contained no forced world selection; all four worlds remained available. The existing changed-profile reward brought XP to 80.
7. Restarted the isolated backend and compared the complete API state: unchanged. Reloaded the final build and checked its catalogue descriptions.

No horizontal overflow was measured at actual CSS widths **375px, 768px and 1279px**. The last is approximately the 1280px target due to the browser's existing zoom. The browser error log was empty. Semantic headings, regions, form labels and keyboard disclosure operation were checked; no full screen-reader audit is claimed.

## Changed files

| Files | Change |
| --- | --- |
| `careerquest/discovery_handoff.py` | New proposal, catalogue validation and versioned handoff service |
| `careerquest/store.py` | Additive handoff table; noncommitting event primitive; public event behavior retained |
| `careerquest/profiles.py` | Atomic confirmation/handoff, validation and idempotency |
| `careerquest/api.py` | Outcome/handoff state, public and confirmed catalogue endpoints, optional selected-world validation |
| `careerquest/discovery_agent.py` | Final outcome in existing graph finish/resume responses |
| `frontend/src/components/DiscoveryOutcome.jsx` | Proposed profile preview and confirmed/public world sections |
| `frontend/src/components/DiscoveryGuide.jsx` | Proposal integration with existing feedback |
| `frontend/src/pages/ExplorerProfile.jsx` | Confirmation explanation and saved handoff receipt |
| `frontend/src/App.jsx` | Career Worlds integration, existing remaining page actions preserved |
| `frontend/src/spec.css` | Scoped responsive proposal/handoff styles |
| `tests/test_discovery_handoff.py` | 19 new backend tests |
| `frontend/tests/discovery-handoff.test.js` | Five new frontend render tests |
| `scripts/smoke_discovery_handoff.py` | Explicitly opted-in live test using temporary fictional storage |
| `README.md`, this report, evidence below | Usage and actual verification results |

No new dependencies, model/provider changes, credential edits, database resets or real student data were introduced. The schema change adds one table. Welcome, quests, existing XP rules, roadmaps/history, tool allowlist and Streamlit fallback were preserved.

## Evidence and limits

- [Live Groq result](test-evidence/discovery-handoff-live.json)
- [Browser checks](test-evidence/discovery-handoff-browser.json)
- [Restart persistence](test-evidence/discovery-handoff-restart.json)
- [Normal database preservation/startup](test-evidence/discovery-handoff-startup.json)
- [Revised proposal](test-evidence/discovery-handoff-proposal.jpg)
- [Confirmed art handoff](test-evidence/discovery-handoff-confirmed.jpg)
- [Final exploratory handoff](test-evidence/discovery-handoff-final.jpg)
- [Exploratory profile on mobile](test-evidence/discovery-handoff-unsure-mobile.jpg)

The browser exercised Not really and Yes; Somewhat was covered by backend tests. Live feedback revisions and a full assistive-technology audit were not repeated in this increment. Streamlit UI startup was not retested. Live admissions/college research remains unimplemented. This remains a local, unauthenticated fictional-student prototype.
