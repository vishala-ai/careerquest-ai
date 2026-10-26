# Five-minute Week 3 demonstration script

**0:00–0:30 — The problem:** High-school students face many pathways. CareerQuest makes exploration playful without pretending to predict their future. Synthetic demo only.

**0:30–1:30 — Gamified profile:** Create fictional Grade 11 student. Complete three quests, earn 60 XP, inspect editable interests. No right/wrong scores.

**1:30–2:25 — Agent and RAG:** Ask about biomedical engineering. Show route trace, curated source IDs, and links. Explain this MVP uses offline keyword retrieval and that links are not live verified. Ollama may choose the next action if enabled; do not claim it generated facts.

**2:25–3:20 — Plan and memory:** Generate and confirm roadmap v1. Save a reflection. Change interests, regenerate and confirm v2. Show both saved events and latest plan.

**3:20–4:10 — Failure handling:** Simulate retrieval failure. The app preserves progress, shows a blocked state, and invents no college facts. Explain bounded tools and no application submission.

**4:10–5:00 — Architecture and learnings:** LangGraph routes to bounded tool execution and stores results; SQLite persists profiles and plans. Future work: live verified college research, accessibility testing, real privacy/authentication controls, and richer multi-step autonomy.

**Demo preparation:** Test Streamlit and Ollama on your Mac. Do not use real student details. Hide desktop notifications. Capture at 1080p if possible. Keep recording under 5 minutes. Verify all shown screens work before filming.
