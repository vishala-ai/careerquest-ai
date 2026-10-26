# Codex continuation prompt — do not rebuild

Read AGENTS.md, README.md, current code and tests. This project already contains a gamified Streamlit UI, SQLite persistence, bounded tool router, curated offline retrieval, optional local Ollama routing and a LangGraph three-node route/execute/finish workflow.

1. Install project dependencies and run Streamlit locally. Fix actual runtime errors and add regression tests; do not claim success without running.
2. Verify LangGraph route -> execute_tool -> finish with an installed version. Add an integration test that asserts selected action and trace. Keep SQLite as authoritative persistence; do not claim graph checkpoints are durable unless added and tested.
3. Test the three-quest journey, XP idempotency, refresh/restart, career source display, roadmap versioning, reflection, and simulated retrieval failure.
4. If Ollama is installed, run a real localhost action-selection smoke test; ensure model failure falls back with a visible trace. No remote API keys or automatic cloud fallback.
5. Add safe, validated multi-step planning only after the basic end-to-end scenario works. For any college-specific facts, verify official sources and dates; never invent admissions deadlines.
6. Add accessible keyboard controls and responsive layouts. Use fictional students only; no public hosting or real minors' data.
7. Update submission documentation with exact commands, actual test counts, screenshots, prompts, iteration notes, limitations, and live demo observations. Report tests passed/failed/skipped/unverified separately.
