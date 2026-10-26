# Welcome page

This is the initial Welcome implementation report. See
[Welcome refinement](WELCOME_REFINEMENT.md) for the current personalized setup,
activity CTA and five-stage journey behavior and its verification.

Replaces the previous Dashboard / Adventure Home with a simple landing page,
as requested. The entry page shows a welcoming introduction, decorative compass
illustration, three static explanations of the experience, and Get Started for
new visitors or Continue My Adventure for returning fictional explorers.
It does not display dashboard statistics, progress charts, a journey map,
roadmap summaries or an activity feed. Its header is simplified; other pages
retain their navigation with the home link renamed Welcome.

Changed: `frontend/src/App.jsx`, `frontend/src/components/AppShell.jsx`.
Added: `frontend/src/pages/Welcome.jsx`, `frontend/src/pages/welcome.css`.
Removed the rendered Dashboard implementation and its page-only stylesheet:
`frontend/src/pages/Dashboard.jsx`, `frontend/src/pages/adventure-home.css`.
The tested progress domain service remains solely to choose the correct resume
destination; its old tests were preserved. Backend services, existing database
records, LangGraph workflows, Streamlit and other page functionality are unchanged.

Exact commands from the project root:

```sh
.venv/bin/python -m unittest discover -s tests -v
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
```

Results: 35 Python tests and 14 frontend tests passed; zero failures or skips.
React production build passed. Chrome checks verified Get Started opens the
existing explorer creation page and Continue My Adventure resumes the existing
selected explorer's appropriate page. Enter-key activation worked. The six-page
navigation on other pages includes Welcome, with no Dashboard entry. The Welcome
page has no primary-navigation dashboard menu or XP header. Actual widths of
375px and 1280px had matching document scroll widths (no horizontal overflow),
with 28px and 36px titles respectively. Browser console error/warning readback
was empty. Viewport overrides were reset; no profile/database write was made
through the browser. Existing loading/error/retry wiring is retained but was not
separately outage-tested again for this simplified page. No live model call or
full assistive-technology audit was performed.

Screenshots:

- [First-visit Welcome](test-evidence/welcome-first-visit.jpg)
- [Returning Welcome](test-evidence/welcome-desktop.jpg)
- [Mobile Welcome](test-evidence/welcome-mobile.jpg)
