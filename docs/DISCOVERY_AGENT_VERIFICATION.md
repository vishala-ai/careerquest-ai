# Student Discovery Agent — assessment, implementation and verification

Verified October 25, 2026 (America/Los_Angeles). Scope: the existing React/FastAPI Discovery Guide and a bounded discovery branch in the existing LangGraph architecture. No separate application or provider was introduced.

## Assessment before implementation

**Discovery Guide was not a tool-selecting agent.** React selected a fixed endpoint; `discovery_guide.generate()` made one structured Groq generation request, then deterministic Python validated/rendered the proposal and matched catalogue records. Feedback branches were fixed UI/service logic. Discovery did not execute `careerquest.graph`.

The **separate career-research workflow** already supported optional Groq action selection through `agent.groq_choose()` and the existing LangGraph route → execute_tool → finish graph. With its Groq option off, it used deterministic keyword routing. It was incorrect to attribute that existing routing capability to Discovery Guide.

This distinction was reported before code changes. Original fixed-service discovery endpoints remain available for compatibility; calling them directly still does not run discovery tool routing.

## What is implemented now

React discovery uses `POST /api/profiles/{pid}/discovery-agent`. The new `build_discovery_graph()` lives in the existing `careerquest/graph.py` beside the unchanged career graph. It routes through four allowlisted named tool nodes:

| Action | Validated behavior |
| --- | --- |
| `ask_clarifying_question` | Select a predefined question about preferences/correction/kept clues, persist it, then return awaiting the student. No unrestricted model-generated question. |
| `revise_discovery_story` | Reuse existing versioned Groq story service, closed vocabulary, source validation and labeled summary fallback. |
| `suggest_career_worlds` | Accept up to three unique approved IDs with backend-validated current choice/preference evidence; return actual catalogue metadata and source references. |
| `request_profile_review` | Request existing Explorer Profile review. It cannot confirm a profile, create a plan or award XP. |

**Genuinely model-directed:** Groq selects among eligible actions; in feedback cases it can ask a question even when a fixed policy would immediately revise. It also selects eligible Career World IDs for the catalogue tool. The selected action controls the LangGraph edge/tool execution; it is not simply a generated label attached to a fixed sequence.

**Deterministic:** prerequisite masks, exact schema checks, source/evidence validation, catalogue metadata, controlled story wording, explicit agreement handling, request/action limits, XP, confirmation gates, safe fallback and the forced review at the three-action cap. Yes agreement always requests profile review under `bounded_policy`; it does not spend a model call pretending that action was model-selected.

The concise story is still rendered with approved Python wording from bounded model-selected building blocks. Neither the new router nor story service is unrestricted narrative generation, live verified research or a fully autonomous research agent.

## Boundaries, feedback and persistence

- Router output must contain exactly `action`, `question_id`, `world_ids`. Pydantic types plus domain checks reject unknown actions, extra fields, unsupported/mismatched IDs, inappropriate inputs and unmet prerequisites. Client requests cannot supply tool names, XP, source choices or confirmation flags.
- Tool outputs are validated against their selected action, actual story row/status, current backend confirmation state and exact approved source/evidence records. Invalid results stop safely without propagating invented sources.
- Somewhat/Not really feedback persists a receipt and explicit preferences/correction in an unconfirmed draft. The model decides clarification versus revision/review within the available-action mask. Incomplete feedback is supported by **Help Me Clarify**. A clarification reply is an explicit preference, not a personality inference.
- Limit: three actions per request, two clarifying questions per saved quest-response set, three feedback revisions across both legacy and agent paths, ten agent request turns per explorer/hour and sixty total/hour. Existing story-generation limits/timeouts remain. Manual editing stays available.
- Each action selection is committed before execution. Completed outputs, source references and pending question state are recorded. Cached repeats/reloads/resumes do not call the model again. Exact repeated feedback does not create another receipt/draft/version.
- Four additive tables store sessions/application state, request turns/process leases, decision/tool receipts and explicit preference evidence. Original quest/feedback/story/profile/roadmap records remain in their existing tables. No raw quest response is overwritten.
- Quest/profile changes invalidate stale sessions/questions/recommendations. A new story created through a legacy endpoint also invalidates older agent recommendation sets. Agreement preserves the accepted recommendation set and its originating method.
- Pending confirmation is derived from the existing persisted profile review state. Declining a confirmed proposal creates an unconfirmed draft immediately, including while clarification is pending. Direct personalized research/roadmap calls remain HTTP 409 until explicit student confirmation. The agent never invokes confirmation or plan tools.
- Routing errors are labeled `bounded_policy_fallback`, with safe error class and HTTP status when available. Story-generation fallback has separate provenance. No alternative provider/model is silently selected. Missing LangGraph uses a visibly labeled bounded service fallback.

The existing `GROQ_MODEL` setting/default `openai/gpt-oss-120b`, key loading and approved endpoint are reused. No key was displayed or changed. Routing prompts use only fictional grade, saved choices, current feedback, bounded tool availability and catalogue evidence; nickname and unrelated history are not sent.

## Recovery claim and limits

Recovery uses **SQLite application checkpoints and tool receipts**, not a native LangGraph checkpointer/interrupt. A persisted selected tool is re-entered through the same graph after restart. An already-saved story is reused if the process stopped before its receipt was committed. Pending student questions are restored without another model call.

A real subprocess test exits after saving a story but before recording the tool output. Another process resumes the selected decision, writes the receipt and finishes the graph. It leaves exactly one completed story, three tool receipts and unchanged XP. The local PID/lease mechanism prevents an active worker from being casually replayed; it does not claim distributed execution or exactly-once upstream HTTP inference during every possible network interruption.

## Changed files

| File | Change |
| --- | --- |
| `careerquest/discovery_agent.py` | New bounded router/tools, strict request/decision/output models, feedback/clarification handling, limits, durable receipts/resume, source and stale-session checks. |
| `careerquest/graph.py` | Discovery graph builder and typed state appended to the existing architecture; original career graph retained. |
| `careerquest/store.py` | Four additive discovery-agent tables. Existing columns and reward functions retained. |
| `careerquest/discovery_guide.py` | Recognize agent preference evidence and share revision counts with the legacy service. Existing generation/action-selection contracts retained. |
| `careerquest/api.py` | Additive profile `discovery_agent` state and validated agent POST endpoint. Existing routes/gates retained. |
| `frontend/src/components/DiscoveryAgentPanel.jsx` | Persisted question UI, activity/provenance panel, typed replies and current-story recommendation projection. |
| `frontend/src/components/DiscoveryGuide.jsx` | Use agent endpoint, send feedback/replies, resume on reload, expose Help Me Clarify and preserve review/manual callbacks. |
| `frontend/src/pages/discovery.css` | Scoped question/activity styling. |
| `tests/test_discovery_agent.py` | Nineteen new mocked-model/real-graph/SQLite tests, including subprocess crash/recovery. |
| `frontend/tests/discovery-agent.test.js` | Six new rendering/projection/provenance tests. |
| `scripts/smoke_discovery_agent.py` | Explicit live tool-selection/resume smoke test using temporary fictional data. |
| `README.md` | Current architecture, deterministic/agentic distinction, limits, recovery and smoke instructions. |

This report, `docs/test-evidence/discovery-agent-*` and regenerated React build assets are also outputs. `careerquest/agent.py`, quest definitions, catalogue content, profile-confirmation code, other page components, Streamlit, credentials and dependencies were not changed. No existing test expectations were weakened or changed.

## Exact commands and final actual results

Run from `/Users/vishalakosaraju/Downloads/careerquest_ai`:

```sh
.venv/bin/python -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=/private/tmp/careerquest-discovery-agent-pycache .venv/bin/python -m compileall -q careerquest app.py tests scripts/smoke_discovery_agent.py
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
.venv/bin/python scripts/smoke_discovery_agent.py --live --output docs/test-evidence/discovery-agent-live.json
```

| Verification | Final result |
| --- | --- |
| Full backend suite | **84 passed; zero failures/skips.** Existing 65 plus 19 agent tests. |
| Full frontend suite | **71 passed; zero failures/skips.** Existing 65 plus 6 agent tests. |
| Backend compilation | Passed, exit 0. |
| React production build | Passed, exit 0. |
| Subprocess crash/recovery | Passed inside the backend suite; no duplicate completed story/XP. |
| Browser walkthrough | Passed with Groq deliberately disabled; truthful bounded fallback, persisted questions, reload/resume, keyboard input and profile review verified. |
| **Live Groq routing** | **Passed:** three actual model-directed decisions and a live follow-up story; details below. |
| Normal API startup | Health `ok`, engine `langgraph`; all pre-existing rows unchanged after restart/readback. |

An early new selector-contract test was accidentally still invoking the fixture's selector mock. The fixture was corrected to exercise the real selector with mocked HTTP transport. It was not a production failure, and assertions were not weakened. No failing or skipped checks remain in the final suites.

### Mocked tests versus live inference

The automated suite mocks all Groq responses. It executes real LangGraph nodes and SQLite operations, tests both feedback branches with complete/incomplete information, invalid actions/fields/world IDs, exact output validation, model timeout/malformed/HTTP failures, safe fallback labels, question caps, request/revision limits, stale quests/profiles/stories, explicit confirmation, plan/history preservation, idempotency, cross-profile resume rejection, missing-graph fallback and source changes during selection.

The **separate live check** used a temporary fictional Grade 11 explorer, Comet Fictional Agent. Only the initial story setup was mocked. Tool routing and subsequent generation were real Groq calls using `openai/gpt-oss-120b`:

1. Not really feedback without preferred interests → Groq selected `ask_clarifying_question`.
2. Student supplied design → Groq selected `revise_discovery_story`; the follow-up story used Groq.
3. Groq selected `suggest_career_worlds` with approved ID `design`.
4. The hard step-cap policy selected `request_profile_review`, labeled `bounded_policy`.

All tool outputs completed and validated. No bounded fallback was needed in this live run. Confirmation remained false, XP stayed 60, raw quest answers were unchanged, a repeated resume used the cached result, and a direct roadmap request returned HTTP 409. Evidence: `test-evidence/discovery-agent-live.json`.

### Browser walkthrough

Chrome used port 18097 and a temporary fictional database with the key deliberately unavailable. Nova Agent Demo completed the existing three quests. The initial graph produced a clearly labeled bounded fallback. Somewhat with incomplete information paused for a correction; reload restored that saved question. The next question collected design. Keyboard activation submitted the answer, the graph revised the story, suggested Digital Product Design and requested review. Activity listed two completed clarification tools, revision, catalogue suggestions and policy review with honest per-step provenance.

Yes then opened the existing Explorer Profile with design selected, still marked Review required. Agent actions preserved all three original choice IDs and 60 XP. Readback found three sessions, five turns, two story versions and exactly two clarification questions. Personalized research and roadmap requests returned HTTP 409. Accepted recommendations survived the Yes transition.

Evidence: `test-evidence/discovery-agent-browser.json`; screenshots `discovery-agent-question.jpg` and `discovery-agent-activity.jpg`. This browser run was **not live inference**.

### Normal application/database preservation

The normal backend was restarted on `127.0.0.1:8000`. Every row in all pre-existing tables was compared before/after startup and a readback; all remained identical. Counts at that check: 5 profiles, 43 events, 7 plans, 42 runs, 6 stories, 5 feedback receipts, 2 adjustments and 5 story-context records. Only four new schema tables were created. No database reset, historical record rewrite or live request against normal student records occurred during restart.

Evidence: `test-evidence/discovery-agent-restart.json`. The isolated test server was stopped after verification; the normal backend remains running.

## Unverified/out-of-scope checks

Native VoiceOver, real mobile hardware, distributed workers/hosts, native LangGraph checkpointer/interrupt behavior, a new Streamlit launch and live failure injection were not exercised. The current browser walkthrough was desktop; new question controls have automated rendering coverage, not a new native-device accessibility certification. Recovery was tested at the documented post-story/pre-receipt crash point and across saved question reload/resume; not every possible interruption during an upstream network call was injected. Other pages retained regression coverage, not a fresh full application walkthrough. Live verified research and production authentication remain outside this prototype.
