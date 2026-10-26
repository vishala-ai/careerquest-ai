CareerQuest end-to-end outcome — October 24, 2026

Historical result from before the interface redesign. The goal-restoration and empty-source-link issues described below were corrected in the later redesign; see [UI redesign verification](UI_REDESIGN.md).

Created exactly one new fictional explorer through the React interface at http://127.0.0.1:8000/. The main journey completed successfully, with two UI issues observed. The profile remains saved and selected in the browser on My Journey.

| Final property | Value |
| --- | --- |
| Nickname | Synthetic E2E Explorer |
| Profile ID | caa9a446-a198-453e-8fc0-38c4948e9824 |
| Grade | 11 |
| Completed quests | 3 of 3 |
| XP | 90: 60 quest XP + 20 for two distinct confirmations + 10 reflection XP |
| Confirmed profile version | 2 |
| Current interests | technology, building, coding, design |
| Saved learning style | Hands-on projects |
| Saved goal | Try a mini-project |
| Saved roadmap versions | 1 and 2 |

| Step/check | Observed outcome |
| --- | --- |
| Create explorer | New fictional Grade 11 profile, 0 XP |
| Explore before confirmation | React displayed the confirmation gate |
| Complete quests | Chose Build a mini-app, Analyze the data, and Build something; reached 60 XP |
| Review/edit profile | All three answers were present. Added coding and selected Try a mini-project |
| Confirm initial profile | Profile version 1, 70 XP |
| Deterministic research | Explore software careers selected research_careers; visible trace method bounded_policy |
| Live Groq career research | Same prompt selected research_careers; visible and persisted trace method groq |
| Live Groq college research | Explore college majors related to technology selected research_college; visible and persisted trace method groq |
| Evidence | Offline descriptions and source metadata appeared, labeled not live verified |
| Propose first roadmap | Proposal appeared without a saved roadmap |
| Explicitly save first roadmap | Saved roadmap version 1 appeared |
| Save reflection | Saved a synthetic reflection about enjoying app building and exploring coding/design; reached 80 XP |
| Repeat unchanged confirmation | Stayed at profile version 1 and 80 XP |
| Revise profile | Removed science, added design, confirmed profile version 2; reached 90 XP |
| Revise roadmap | New proposal appeared while saved version 1 remained intact; explicit save created version 2 |
| Simulated research outage | With deterministic routing, result reported research unavailable; trace showed ConnectionError, no source results |
| Browser reload | Nickname, grade, 90 XP, confirmed interests, profile version 2, reflection, journey, and saved roadmap version 2 remained |
| API duplicate quest check | HTTP 409; no additional XP |
| API unchanged confirmation check | HTTP 200; profile version 2 and 90 XP unchanged |
| API tampered roadmap check | HTTP 409; original saved version 2 and profile unchanged |

The final roadmap contains five exploratory activities: compare two pathways using cited sources; try a mini-project and reflect; verify program prerequisites on official websites; compare affordability and major fit with a counselor; and try a small project inspired by Explore Occupations. These are template suggestions, not admissions requirements or predictions.

Two UI issues remain:

1. After reload, the goal dropdown displayed Explore careers and college majors rather than the saved Try a mini-project. My Journey and the persisted event still retained the correct goal. The learning-style dropdown used its default throughout this scenario, so a nondefault learning-style reload was not tested here.
2. The College Pathway Checklist has no external URL in the offline catalog, but React rendered it as a clickable source link pointing back to the application. Such illustrative records should be displayed as source text rather than external links.

Browser interactions covered the main journey. Targeted HTTP checks covered duplicate and tampered submissions; read-only SQLite queries were restricted to the newly created synthetic profile to verify its saved run traces and roadmap versions. No application code was changed, no existing profile was deleted, and no database was reset. The only new repository files are this report and the local evidence files below. Reload persistence was verified; no backend restart was performed during this scenario.

Evidence:

- [Final journey screenshot](test-evidence/synthetic-e2e-journey.jpg)
- [Saved roadmap screenshot](test-evidence/synthetic-e2e-roadmap.jpg)
- [Final synthetic API state](test-evidence/synthetic-e2e-state.json)

Groq selected actions only. Career and college evidence remained offline; live verified research is not implemented. No real student information was used.
