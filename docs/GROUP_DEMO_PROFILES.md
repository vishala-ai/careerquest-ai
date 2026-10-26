# CareerQuest group-demo explorers

Eight fictional explorers are saved in the working application: two per grade, 9–12. Their names begin with `Demo G9`, `Demo G10`, `Demo G11` or `Demo G12` for easy selection. These are prepared demonstration fixtures, not real student submissions or AI-generated biographies.

Open http://127.0.0.1:8000/, refresh an already-open tab, then use the **student profile menu → Switch Explorer**. All eight were created through the UI and registered in the current browser. The demo selector tab is open with Canvas Comet selected.

| Grade | Saved explorer name | Interest focus | Suggested catalogue worlds |
| --- | --- | --- | --- |
| 9 | Demo G9 - Canvas Comet | art, creative, design | Software Development, Digital Product Design |
| 9 | Demo G9 - Nature Scout | nature, biology, research | Biomedical Engineering, Environmental Science |
| 10 | Demo G10 - Byte Builder | coding, math, building | Biomedical Engineering, Software Development |
| 10 | Demo G10 - Design Wave | art, design, people | Digital Product Design |
| 11 | Demo G11 - Bio Prism | biology, engineering, science | Biomedical Engineering, Environmental Science |
| 11 | Demo G11 - Climate Grove | nature, research, helping | Environmental Science |
| 12 | Demo G12 - Systems Orbit | technology, coding, engineering | Biomedical Engineering, Software Development, Digital Product Design |
| 12 | Demo G12 - Creative Flux | creative, design, people | Software Development, Digital Product Design |

Each explorer starts with:

- Three saved discovery quest responses and an explicitly seeded, confirmed Explorer Profile.
- 70 XP from the existing rules: 20 per first quest completion plus 10 for initial profile confirmation. Creation itself awarded no XP.
- Zero researched/shortlisted careers, zero saved path preferences and zero portfolio versions. Nothing is selected automatically for a permanent career.
- No pre-generated Discovery Story and no invented AI output. Career World suggestions are the existing deterministic matches to the confirmed interests. No Groq request was needed for preparation.

Suggested demonstration:

1. Pick an explorer in Switch Explorer. Home displays its saved nickname, grade, points and next action.
2. Review saved answers in Discover and the confirmed interests in Explorer Profile. The existing Discovery Guide can be demonstrated separately; live Groq inference was not tested while preparing these fixtures.
3. Open Explore Careers, read Why suggested, compare supported careers and research one.
4. Explicitly save a career to the shortlist. Choose a primary/optional secondary path or I’m Still Exploring, and save those preferences.
5. Continue through the emerald milestone, review the graphical portfolio, explicitly confirm/save it, then download its version-specific PDF.
6. To demonstrate corrections, use Explorer Profile → Edit Profile. New personalized research remains blocked until the updated profile is explicitly reconfirmed.

Demo actions persist. Use another prepared explorer for a fresh starting point rather than recreating a profile with the same name. The switcher remembers profiles in this browser; another browser/device will not automatically inherit that local list.

Verification: **8/8** profiles selected successfully in the UI; exactly **2 per grade**; all interests, confirmations and earned points verified through the API. The five previous profiles and every pre-existing database row remain unchanged. Only 8 profiles, 24 quest events, 8 confirmation events and 8 validated handoffs were added. Schema and application code were unchanged. No build/test-suite rerun was needed for this data-only task; verification covered the saved records, every switcher selection and one personalized Career Worlds view.

[Saved choices and IDs](GROUP_DEMO_PROFILES.json) · [Verification](test-evidence/group-demo-profiles-verification.json) · [Roster screenshot](test-evidence/group-demo-explorers.png).
