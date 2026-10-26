# CareerQuest AI — High School to College Adventure

The React/FastAPI app now requires username/password login. Visitors register an alias-only demo account, create one Explorer, and resume their own persisted progress after signing in. Authentication uses Argon2id, server-side sessions, CSRF protection and server-side profile ownership, including PDF/legacy routes. Existing unassigned local profiles stay private; the host can assign credentials with `scripts/account_admin.py`. Account/profile creation grants no XP and never confirms interests.

For a new Replit project, see [cloud deployment instructions](docs/CLOUD_DEPLOYMENT.md). Local SQLite is retained; published Replit deployments require persistent PostgreSQL and a configured HTTPS origin. The source-only import ZIP excludes local records and secrets. This remains a test-data-only educational demo; actual student data is outside this project’s scope.

Adventure Home now has portfolio-aware messaging and a brighter four-stage trail. The shared header has one four-item navigation menu; its duplicate progress strip is removed. Current saved portfolios show a completed trail with View My Portfolio, while older snapshots remain distinct and revisitable. See [focused Home/header verification, diff and screenshots](docs/HOME_HEADER_REFINEMENT_VERIFICATION.md).

Explore Careers now saves career/path preferences, including an explicit undecided choice, before the emerald milestone. My Portfolio assembles a visual preview without repeated path controls; explicit confirmation saves an immutable version with a version-specific PDF download. See [portfolio flow changes, exact test results and limitations](docs/PORTFOLIO_FLOW_VERIFICATION.md).

The shared student UI now uses four primary destinations: Home, Discover, Explore Careers and My Portfolio. The shared header shows saved identity and Explorer Points; the full Discover → Confirm → Explore → Celebrate trail is on Home. Profile review/switching and earlier activities remain in the student menu. See [global UI changes, exact test results and browser limitations](docs/GLOBAL_UI_VERIFICATION.md).

Career Worlds now leads through an emerald Career Discovery Milestone before portfolio controls, with backend-derived counts, server-checked eligibility and a read-only visual map of saved choices. Viewing or entering does not save a portfolio or award points. See [implementation, changed files and actual verification](docs/CAREER_WORLDS_VERIFICATION.md#current-increment-emerald-career-discovery-milestone).

Career Worlds celebrates six persisted exploration milestones with personalized, supportive cards and contextual next actions. Explicit portfolio review saves a completed snapshot; delivery/dismissal is persisted and no new XP or badge rules are introduced. See [celebration verification](docs/CAREER_WORLDS_VERIFICATION.md#previous-increment-personalized-career-celebrations).

Career Worlds opens with up to three supported recommendations from current confirmed interests, followed by the remaining catalogue. Students can compare two or three careers, explicitly shortlist them and save versioned primary/optional secondary exploration paths. Top navigation returns to recommendations; saved details resume only by explicit choice. See [recommendations and paths verification](docs/CAREER_WORLDS_VERIFICATION.md#previous-increment-recommendations-first-and-exploration-paths).

Career Worlds separates the student interface from local developer tools. Developer traces/failure simulation are disabled by default and guarded server-side for explicitly enabled, direct local testing only. See [access configuration and verification](docs/CAREER_WORLDS_VERIFICATION.md#previous-increment-studentdeveloper-separation).

Discovery Quests now ends with one profile-review CTA. Yes / Somewhat / Not really feedback, revisions, manual edits and explicit confirmation live together on Explorer Profile. See [single-review verification, changed files and actual results](docs/PROFILE_REVIEW_VERIFICATION.md).

The Discovery Agent now returns a story, editable proposed profile, evidence-linked Career Worlds and an optional mission. Explicit profile confirmation creates a versioned SQLite handoff; edits require reconfirmation, and uncertain explorers need no career selection. All catalogue worlds remain open. See [handoff verification and actual test results](docs/DISCOVERY_HANDOFF_VERIFICATION.md).

**Week 3 synthetic-only prototype.** Interactive gamified discovery quests, a bounded LangGraph Student Discovery Agent, XP, career exploration, grade 9–12 roadmap, reflection, SQLite persistence, and bounded agent tool selection. Optional Groq action routing selects one allowed action; the Discovery Guide has its own structured generation contract. Source pages are *not checked live*. No actual student accounts, admissions predictions, or applications.

## Run on Mac

```bash
cd careerquest_ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py --server.address 127.0.0.1
```

For optional Groq action selection, set `GROQ_API_KEY` in the backend process environment before starting FastAPI or Streamlit, then enable **Use Groq for action selection (cloud)**. The default model is `openai/gpt-oss-120b`, using strict JSON-schema output and backend action validation. `GROQ_MODEL` can override it. No additional SDK is required.

On macOS/zsh, enter the key without displaying it or recording it in shell history:

```zsh
read -rs 'GROQ_API_KEY?Groq API key: '
export GROQ_API_KEY
printf '\n'
.venv/bin/python -m uvicorn careerquest.api:app --host 127.0.0.1 --port 8000
```

The key belongs only in the backend environment or the project-root `.env`, never in React, a `VITE_` variable, source control, or chat. The backend loads the project-root `.env` automatically; existing process environment variables take precedence. Restart the backend after setting/changing the key. On hosted development environments, configure it through the provider's server-side environment settings.

For action selection, Groq receives only the synthetic question (up to 800 characters), grade, and interests; it selects one allowed action. Retrieval and roadmap generation still use the offline catalog and deterministic templates. Live verified research is not implemented. With the action-selection checkbox off, career-guide routing makes no Groq request. Missing credentials, API errors, timeouts, or invalid output fall back to deterministic routing and are recorded as `bounded_policy_fallback` in the trace. Successful model selection is labeled `groq`. Discovery Guide generation is a separate request described below.

A rejected model request uses the deterministic fallback and does not silently switch cloud models.

If `GROQ_MODEL` is already set, it takes precedence over the default. To explicitly select the default model in the terminal that starts the backend:

```sh
export GROQ_MODEL="openai/gpt-oss-120b"
```

See [Groq structured outputs](https://console.groq.com/docs/structured-outputs) and [API reference](https://console.groq.com/docs/api-reference).

## Run tests (no model or Streamlit needed)

```bash
python -m pip install -r requirements-api.txt httpx
python -m unittest discover -s tests -v
```

## Demo script (under five minutes)

1. Create fictional Grade 11 student.
2. Complete three quests and earn 60 XP. Explain that interests are exploratory clues, not a test score.
3. Open Career Worlds, ask about biomedical engineering, inspect source IDs and links.
4. Generate a Grade 11 roadmap, confirm and save it, save a reflection, edit interests, then propose and confirm version 2.
5. Turn on simulated research failure and show the agent preserves state and does not invent information.
6. Show Agent Trace and discuss allowed tool routing, persistence, and human boundaries.

## Actual implementation boundaries

- **Working core:** SQLite profile/event/plan history, bounded tool router, source-tagged offline retrieval, game progression, XP, roadmap versions, simulated tool outage.
- **Verified locally after the Groq migration:** 31 Python tests plus 7 frontend journey tests, including LangGraph and mocked Groq contracts/failures; backend compilation; offline core smoke; React production build; localhost API journey and restart persistence with a temporary synthetic database; live `openai/gpt-oss-120b` selection through FastAPI and LangGraph using project `.env` settings.
- **Still needs verification:** Streamlit UI startup. The redesigned React interface has been exercised in a desktop browser and at a 390-pixel CSS viewport. Automated unit tests use synthetic credentials; the separate live smoke check uses the locally configured Groq key without displaying it.
- **Not implemented:** live college admissions retrieval, authenticated student access, real minors' data privacy controls, external actions, vector database, college applications, scholarship/internship applications, production counselor portal.
- **Agent behavior:** a bounded router selects one action from an allowlist. When Groq is enabled, it selects the action via structured output. This is an early-stage tool-selecting agent, **not** a fully autonomous multi-agent research system.

## Privacy

Share the alias-only demo only after completing the cloud deployment checks. Do not collect real student information. Password login provides account isolation; it does not make this prototype a production student system. Streamlit remains a local fallback and must not be exposed as an unauthenticated public alternative.

## Files

- `app.py`: Streamlit interface
- `careerquest/agent.py`: bounded action selection, optional Groq, error handling
- `careerquest/store.py`: SQLite event and plan persistence
- `careerquest/catalog.py`: curated retrieval with source metadata
- `careerquest/graph.py`: optional LangGraph wrapper
- `data/knowledge.json`: small curated illustrative knowledge base
- `tests/`: offline unit tests
- `docs/`: submission and demo notes

## LangGraph execution

When `langgraph` is installed, the Streamlit app uses `careerquest.graph.run_graph` (route → execute_tool → finish). The graph itself is compiled per request; **SQLite profile, event, plan, and run records are persistent, but LangGraph checkpoint persistence is not implemented**. Without LangGraph, the core bounded agent runs and the sidebar labels the fallback.

## Human confirmation boundary

A proposed roadmap is **not saved automatically** by the agent. The student must click **Confirm and save roadmap** after reviewing its suggested activities. Reflection events are saved only after the student explicitly clicks **Save reflection**. The demo does not include a LangGraph interrupt/checkpoint-based approval workflow; this UI confirmation is the current human boundary.

## New: Gamified React interface + FastAPI (Week 3)

The React frontend in `frontend/` now centers on a visual six-stop journey map, an explorer passport, a guided next step, and a human-readable activity timeline. Explorer setup creates an account-owned demo profile with a nickname, grade selection and an avatar. Sign Out / Switch Account replaces the browser-only profile selector in the authenticated app. FastAPI remains the adapter at `careerquest/api.py`. It retains the existing Python agent, synthetic career catalog, and Streamlit fallback. The new UI adds an explicit student **Review & Confirm My Explorer Profile** gate between the three quests and personalized research/planning. See `docs/REACT_REPLIT_SETUP.md` for setup, limitations, and Replit guidance.

See [the UI redesign verification](docs/UI_REDESIGN.md) for the checked flows, screenshots, and current profile boundaries.

For Replit, use the source-only import package and single-port startup configuration described in [Replit setup](docs/REACT_REPLIT_SETUP.md). The local database and `.env` are excluded from the package and remain unchanged. [replit.md](replit.md) tells Replit Agent which implementation and specification checkpoint to preserve.

## UI specification implementation

The full [target UI/UX specification](https://docs.google.com/document/d/1eKs2o8w3tMGNiXEEtQmLSXZwJwCepsIrgDkrxufst2w/edit) was read and retained with source metadata in `docs/reference/UI_SPECIFICATION.txt`. The first increment aligns Dashboard, Discovery Quests, and Explorer Profile, with six-page navigation, editable quest responses, unique quest XP, event-backed profile drafts, and a server-side reconfirmation gate. See [the increment-one report](docs/SPEC_INCREMENT_1.md) for exact checks and remaining work. The remaining pages retain their existing behavior and are not yet claimed to meet the full specification.

## Discovery Guide

After the three saved quests, React uses `POST /api/profiles/{pid}/discovery-agent` to run the bounded discovery graph. Its story tool reuses the versioned Discovery Guide and its **separate Groq structured output contract** using the existing `GROQ_MODEL` configuration (default
`openai/gpt-oss-120b`); action selection is unchanged. Groq selects evidence-linked
interpretations, activities and up to three Career Worlds from a closed approved
vocabulary. The server validates exact saved choices and catalogue tags, then
renders a friendly 70–110 word summary, up to three interest clues and one optional mini-mission with approved tentative wording. It does
not accept unrestricted model prose or claim diagnoses, ability, achievements,
career-fit scores or admissions outcomes.

Initial generation sends only the fictional explorer's grade and saved quest choices/IDs with the approved vocabulary. Revisions also send the current correction and explicitly selected/kept interests; reviewed profile interests can supply authoritative evidence. The saved nickname stays in the local heading. Unrelated feedback, roadmap history and other profile fields are not sent.
Invalid or unavailable model output produces a visibly labeled **Deterministic
Discovery Summary — Not AI-generated**. Source links remain curated/offline.

SQLite stores story versions, source-response hashes and snapshots, model ID,
generation status, and feedback separately from XP/profile confirmation events.
Quest or profile changes make old versions stale; new proposals archive earlier recommendation sets. Returning to discovery shows/generates the current version while preserving history. React submits feedback to the discovery agent. Yes saves agreement and requests profile review under deterministic policy. For Somewhat or Not really, Groq can select a clarifying question, a story revision, catalogue suggestions or profile review within validated prerequisites. Help Me Clarify supports incomplete feedback. Replies and preferences are saved in an unconfirmed profile draft. The older `/discovery-guide`, `/feedback` and `/revise` routes remain compatible fixed-service endpoints; calling them directly does not run model-directed discovery routing. Three feedback revisions are allowed per saved quest-response set; Edit Interests Manually remains available. No feedback confirms the Explorer Profile. Existing confirmation gates still apply to personalized research and roadmaps.

Generation requests are reserved atomically before network I/O, capped at five
per explorer/hour and thirty total/hour, including failed attempts. Cached reads
make no model request. An explicit retry creates another bounded attempt/version.
Feedback is capped at twenty changes per explorer/hour. These limits persist
across process restarts; the API requires account ownership for access. Local SQLite remains supported.

For one explicitly labeled live check, using a temporary fictional database:

```sh
.venv/bin/python scripts/smoke_discovery_guide.py --live
```

A valid but empty model world list now uses a separately labeled catalogue fallback; an empty catalogue or unmatched preference shows an honest unavailable state. Model/status/validation information lives under How this was generated.

See `docs/DISCOVERY_STORY_WORKFLOW_VERIFICATION.md` for current tests, browser results and one successful live Somewhat revision. `docs/DISCOVERY_GUIDE_VERIFICATION.md` records the earlier initial-generation live-provider check. Live Not really generation and live failure injection were not exercised.


## Student Discovery Agent: what is genuinely agentic

Before this increment, Discovery Guide called one fixed Groq generation function;
it did not use LangGraph or select tools. The older career-research graph already
had optional model-directed action routing. React discovery now uses a separate
branch in the **same `careerquest/graph.py` LangGraph architecture**, selecting only:

- `ask_clarifying_question`
- `revise_discovery_story`
- `suggest_career_worlds`
- `request_profile_review`

Groq chooses eligible tools and approved world IDs through strict structured
output. Python validates exact fields, prerequisites, source evidence and tool
outputs. Yes agreement and the hard step-cap review action are deterministic
policy, explicitly labeled `bounded_policy`. Invalid/unavailable model decisions
use `bounded_policy_fallback`; story-generation provenance is labeled separately.
Rendering, XP integrity, catalogue matching, safety gates and final student
confirmation remain deterministic. This is not unrestricted autonomous research.

Each request permits at most three tool actions. At most two clarifying questions
and three feedback revisions are permitted per saved quest-response set; manual
editing remains available. Agent requests are capped at ten per explorer/hour
and sixty total/hour, in addition to existing story-generation limits. Cached
resume/reload does not make another model request.

SQLite persists sessions, request turns, selected/completed tool receipts,
explicit preferences and pending questions. A decision is saved before its tool
runs. A new process can resume the selected operation and reuse its saved story
rather than award duplicate XP or generate another completed version. This is
**application-level SQLite recovery**, not a native LangGraph checkpointer or
interrupt workflow. The local process lease does not claim distributed execution.

The agent cannot confirm a profile or create a personalized roadmap. Explicit
student confirmation through the existing profile API remains mandatory. An
Activity disclosure distinguishes actual Groq decisions, policy actions, bounded
fallbacks, tool failures and catalogue sources. Live verified research remains
unimplemented.

For the reproducible live routing check with a temporary fictional database:

```sh
.venv/bin/python scripts/smoke_discovery_agent.py --live --output docs/test-evidence/discovery-agent-live.json
```

See `docs/DISCOVERY_AGENT_VERIFICATION.md` for the before/after assessment, exact
test results, restart/resume evidence and remaining verification limits.
