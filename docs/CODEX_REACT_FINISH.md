# Codex — final verification task

Read AGENTS.md and docs/REACT_REPLIT_SETUP.md. Do not rebuild the agent. Preserve the existing Streamlit fallback.

1. Install Python dependencies from requirements-api.txt and npm dependencies from frontend/package.json. Record versions and create/commit the package-lock.json produced by a successful npm install.
2. Run `python -m unittest discover -s tests -v` and confirm LangGraph test executes, not skips.
3. Run `npm run build`; fix JSX or build errors without weakening profile-confirmation checks.
4. Start FastAPI and React, manually exercise: new fictional Grade 11 student → 3 quests → editable profile summary → confirm → career exploration → roadmap proposal → roadmap confirmation → reflection.
5. Reload and confirm persistence. Test duplicate quest click, unconfirmed profile, modified roadmap payload, and simulated retrieval failure.
6. Verify model-selection trace truthfully reports when Ollama is unavailable and uses the bounded fallback. Do not claim local Ollama is running without a live smoke test.
7. Do not deploy or publish until actual authentication, synthetic-only enforcement, rate limits, and access controls are in place. Do not add real student records.
8. Update Week 3 documentation with actual UI screenshots, exact tests, tool failures, and known limitations. Record video ≤5 minutes.

Report passed, failed, skipped, and unverified checks separately.
