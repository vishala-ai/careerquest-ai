# Discovery Story and feedback workflow refinement

Verified October 24, 2026 (Pacific). This increment changes only the Discovery Story/feedback workflow and its integration with existing profile review. Quests, XP policy, catalogue records, other page components, action selection, LangGraph and Streamlit were preserved.

## Diagnosis of the empty Career Worlds screen

The current normal database contained a story with `status: groq`, `error_type: null`, saved interests `technology`, `science`, `research`, and an empty `career_worlds` array. All four approved career records have supporting catalogue tags for at least one of those choices. The previous schema/domain validator permitted zero recommendations, and a valid empty result was cached without a catalogue fallback. That explains the screen; there was no recorded validation rejection or ID mismatch in this record. The original raw provider response/reasoning was not retained, so no claim is made about why the model chose an empty array.

Evidence: `test-evidence/story-refinement-diagnosis.json`. The historical row was inspected read-only and retained unchanged.

The refined path requests supported worlds, validates every ID/evidence reference, and handles valid empty output separately from invalid output. An empty list uses a deterministic, tag-supported catalogue fallback when possible, visibly labeled **Catalogue-based suggestions · Not Groq-generated**. A genuinely empty catalogue or unmatched stated preference shows an honest unavailable state. There is no hardcoded recommendation list or substituted provider.

## Delivered behavior

- The heading uses the saved nickname, with Explorer as a neutral fallback. The student-facing summary is 70–110 words (90 words initially and 93 words in the revised browser fixture), followed by up to three interest clues and one optional mini-mission. Raw answers are not repeated across three story sections.
- Model ID, generation status, source inputs and safe validation reason codes are inside the closed-by-default **How this was generated** disclosure. Saved answers remain inspectable there; the existing Discovery Clues cards and quest editor are preserved.
- Up to three approved catalogue worlds include short explanations and supporting saved-choice or explicitly stated-preference references. Titles/source metadata/URLs come from the existing catalogue. Sources remain curated/offline, not live verified.
- **Yes:** save agreement and navigate to Explorer Profile review. No automatic confirmation or XP award.
- **Somewhat:** require a trimmed correction of at least three characters. Students explicitly keep the clues they agree with and can add preferred interests, up to three combined clues/interests. Keeping a clue without adding a new interest is supported. The revised proposal shows kept/added/set-aside clues and the verbatim correction.
- **Not really:** ask for preferred interests and generate from those stated preferences, setting earlier inferences aside. A custom interest with no catalogue match remains valid as a preference; it does not receive a fabricated recommendation.
- Revisions persist a feedback receipt, an adjustment/evidence record, a new story/context version and an **unconfirmed** profile draft. Raw quest history and prior confirmed profile/roadmap records are retained. No feedback confirms an Explorer Profile. Personalized research/planning remains server-gated until explicit profile confirmation.
- Three feedback revisions are allowed per saved quest-response set, in addition to the existing per-hour model request limits. Repeated identical revision requests are idempotent. Failed preflight/limit requests make no partial feedback/draft writes.
- **Edit Interests Manually** remains available after the revision cap or model errors and carries selected or still-typed interests into the existing editable profile draft. The normal profile editor can retain more than three interests; all eligible stated interests remain recommendation evidence even though the story shows only three clues.
- Context signatures include saved quests, reviewed/draft profile state and active correction evidence. Quest/profile changes stale older stories; any newer proposal archives earlier recommendation sets. Old versions are preserved and cached reloads do not award XP or create duplicate proposals.

The model continues selecting bounded narrative building blocks through Groq (`GROQ_MODEL`, default `openai/gpt-oss-120b`); Python renders the concise approved wording. There is no unrestricted model prose, diagnosis, aptitude score, career-fit percentage or admissions prediction. Explicit preference IDs restrict revised outputs; a model that cites rejected old inferences is rejected and replaced by labeled deterministic content.

Initial generation sends grade and saved choices/IDs plus the approved vocabulary. Revision generation additionally sends only current explicit preferences/kept interests and the current correction, capped at 500 characters. Nickname, XP, unrelated feedback, roadmap history and unrelated profile fields are not sent. Fictional data only; existing keys/provider configuration were reused without displaying credentials.

## Changed files

| File | Change |
| --- | --- |
| `careerquest/discovery_guide.py` | Concise story projection, preference-backed evidence, empty-world fallback, safe rejection codes, context signatures, atomic feedback/revision reservation, revision cap, profile-draft integration and recommendation invalidation. |
| `careerquest/store.py` | Additive `discovery_adjustments` and `discovery_story_context` tables. Existing table columns/rows and XP functions retained. |
| `careerquest/api.py` | Validated revision body and `/api/profiles/{pid}/discovery-guide/{sid}/revise` endpoint; existing feedback receipt endpoint retained. |
| `frontend/src/components/DiscoveryGuide.jsx` | Nickname summary, compact clues/mission, provenance disclosure, three feedback branches, explicit preferences, change summary, manual escape path and version history. |
| `frontend/src/pages/DiscoveryQuests.jsx` | Pass guide review/refresh callbacks; quest behavior retained. |
| `frontend/src/App.jsx` | Scoped guide callbacks refresh state, open existing profile review/manual draft and avoid applying a late response to another explorer. |
| `frontend/src/pages/discovery.css` | Scoped story, clue, preference, change-summary and responsive control styling. |
| `tests/test_discovery_feedback_workflow.py` | Fourteen new mocked backend workflow tests. |
| `frontend/tests/discovery-guide-render.test.js` | Six new rendering tests; original four assertions/tests retained. |
| `README.md` | Current data flow, feedback endpoints, limits, provenance and verification documentation. |

This report, `docs/test-evidence/story-refined-*`/`story-refinement-diagnosis.json`, and the regenerated React build are verification artifacts. No catalogue, quest definition, `.env`, action-selection contract, LangGraph graph or Streamlit code was changed. Explorer Profile's existing component and explicit confirmation API were reused.

## Commands and final actual results

From `/Users/vishalakosaraju/Downloads/careerquest_ai`:

```sh
.venv/bin/python -m unittest tests.test_discovery_feedback_workflow -v
.venv/bin/python -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-story-pycache .venv/bin/python -m compileall -q careerquest app.py tests
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
.venv/bin/python /private/tmp/careerquest-story-revision-live.py
```

The last command was an explicitly labeled one-request live smoke script, separate from the automated tests. It used a temporary fictional database and a mocked initial proposal only for setup; the revision provider call was real. Its sanitized evidence is retained in the repository.

| Check | Actual result |
| --- | --- |
| Full backend suite | **65 passed**, zero failures/skips. Existing 51 plus 14 new workflow tests. |
| Full frontend suite | **65 passed**, zero failures/skips. Existing 59 plus 6 new rendering tests. |
| Backend compilation | Passed, exit 0. |
| React production build | Passed, exit 0. |
| Browser workflow | Yes, Somewhat, Not really, reload, revision cap, manual editing and typed-interest preservation passed in an isolated fictional fallback fixture. |
| Responsive browser checks | No horizontal overflow at exact 375/768/1280 CSS-pixel iframe widths, including correction and preference controls. |
| **Live Groq revision** | **Passed**, one actual `openai/gpt-oss-120b` Somewhat request; details below. |
| Normal backend restart | Health `ok`, engine `langgraph`; all pre-existing rows unchanged after startup/readback. |

No existing test expectations were weakened or changed. No unresolved failures or skipped automated tests remain.

### Mocked backend/frontend coverage

Covers concise word count, source fidelity, valid/invalid/empty model world lists, fabricated choices, catalogue-tag evidence, separate fallback provenance, malformed JSON, timeout, empty catalogue, unknown preferred topics, preference-overriding model rejection, Yes receipt integrity, Somewhat required correction and retained-only clues, Not really replacement, history/reload persistence, confirmed-profile and roadmap preservation, no automatic confirmation, revision/request limits, idempotency, manual editing after the cap, profile/story invalidation and more than three manually entered preferences. The original suite retains XP, routing, LangGraph, SQLite and confirmation-gate coverage.

### Browser observations — fallback, not live inference

Chrome used localhost port 18096 with the key deliberately unavailable and a temporary database. One fictional Grade 11 explorer, **Nova Story Demo**, completed Build a mini-app / Analyze the data / Build something.

1. The initial 90-word nickname story showed three clues, one mini-mission and clearly labeled catalogue suggestions. Technical details were collapsed.
2. Yes opened **Does this feel like you?**, still marked Review required, without confirming or increasing the 60 XP.
3. Somewhat required a correction. Keeping technology and adding art produced version 2 with visible Kept / Added / Set aside / correction details. Reload restored it without another version or XP.
4. Not really with design produced version 3 using design only; its world was Digital Product Design, supported by stated preference evidence.
5. A music preference produced version 4 with an honest no-supported-match state. After three revisions, the guided revision CTA was disabled while manual editing remained available.
6. Keyboard activation of manual editing carried biology into the existing unconfirmed profile editor. Returning to discovery created a fresh profile-backed version 5 and archived prior recommendation sets.
7. Manual editing also preserved a still-typed, not-yet-added astronomy interest after the revision cap. It reached the existing profile editor as a selected unconfirmed preference.

Readback found exactly three unique original quest completions, unchanged saved choice IDs/content across story versions, total/quest XP 60 and no profile confirmation. Direct roadmap and exploration requests returned HTTP 409. Feedback receipts retained Yes, Somewhat and both Not really responses. No browser fixture operation called Groq.

### Live inference — explicitly separate

A temporary **Comet Fictional Revision**, Grade 11, used a deterministic mocked initial proposal, followed by **one actual live Somewhat revision**. It asked to keep technology and explore art instead of science. Groq returned valid structured output using `openai/gpt-oss-120b`, kept technology, added art, and selected `design` (Digital Product Design). It passed evidence validation without recommendation fallback. The summary contained 93 words, the previous proposal was retained, raw quest answers stayed unchanged, XP stayed 60, confirmation remained false and a direct roadmap proposal returned HTTP 409.

Evidence: `test-evidence/story-refined-live-revision.json`. This is not a claim that all branches or failures were tested against the live provider.

### Normal database preservation

The normal API was restarted on `127.0.0.1:8000` with final backend code. Every row in every pre-existing table was compared before and after restart/readback and remained identical: 5 profiles, 40 events, 7 saved roadmap rows, 42 runs, 1 story and 1 feedback row at that check. Only two additive schema tables were created; no history was rewritten, profile replaced or database reset. No live request was made against normal records during restart.

## Evidence and unverified checks

- `test-evidence/story-refinement-diagnosis.json`
- `test-evidence/story-refined-browser.json`
- `test-evidence/story-refined-responsive.json`
- `test-evidence/story-refined-live-revision.json`
- `test-evidence/story-refined-restart.json`
- Screenshots: `story-refined-summary.jpg`, `story-refined-somewhat.jpg`, `story-refined-manual-profile.jpg`, `story-refined-375.jpg` in `test-evidence/`.

Native VoiceOver, native reduced-motion settings, real mobile hardware, live Not really generation and live failure injection were not exercised. Provider errors/empty catalogues were tested with mocks; the interactive browser used deterministic fallback, while one Somewhat revision used live inference. Streamlit was not relaunched. Production authentication/real-student support and live-verified career/college research remain outside this scope. The isolated test server was stopped after verification; the normal backend remains available.
