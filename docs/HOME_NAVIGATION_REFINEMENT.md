# Adventure Home — one primary journey controller

First-time setup now uses a separate Create My Explorer → Welcome aboard /
First Mission flow. Returning Home retains the single Trail CTA described here.
See the current [Welcome-state verification](WELCOME_STATES_VERIFICATION.md).

Refined Adventure Home only. The purple hero container, compass illustration,
rounded styling and Adventure Trail layout remain. The hero now welcomes the
explorer and summarizes saved progress; **the Trail contains the single prominent
next-activity CTA**. Other pages' behavior, routes, backend services, schema,
LangGraph workflow and confirmation gates were preserved. No writes were made
to the normal application's database during verification.

## Changed files

- `frontend/src/pages/Welcome.jsx`: removes hero navigation buttons, makes the
  saved nickname greeting the H1, displays progress-aware motivational copy and
  saved grade/earned Explorer Points, and keeps first-time setup fields without
  a duplicate submit button.
- `frontend/src/welcomeHero.js`: new read-only copy/metadata projection of the
  backend response. Reconfirmation takes priority over saved-roadmap messaging.
  Missing grade/XP values are omitted; a real saved zero is displayed.
- `frontend/src/components/StudentTrail.jsx`: new-student submission uses the
  highlighted milestone's existing primary button. Its HTML `form` association
  submits the setup fields above without adding a second CTA. Returning-student
  routing, recommendation, completion and revisit behavior remain unchanged.
- `frontend/src/components/AppShell.jsx`: Switch Explorer appears only in the
  Home header as a secondary outlined control. Other pages retain their existing
  StudentHeader and main navigation.
- `frontend/src/App.jsx`: passes the existing busy state to that header control.
  Existing route handlers and backend requests remain unchanged.
- `frontend/src/pages/welcome.css`: scoped metadata badges and responsive Home
  header switcher styles. No other page stylesheet or layout was changed.
- `frontend/tests/welcome-hero.test.js`: six new progress-message, metadata and
  read-only-state tests.
- `frontend/tests/welcome-render.test.js`: six new actual-JSX rendering checks for
  a single Trail CTA, zero hero navigation controls, external form association,
  header-only Switch Explorer and preserved other-page header controls.
- This report, a link from the previous trail report and `home-single-cta-*`
  verification evidence.

## Actual verification results

Commands executed from the project root:

```sh
.venv/bin/python -m unittest discover -s tests -v
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
```

Final results: **35 backend tests passed; 38 frontend tests passed; production
build passed. Zero final test failures or skips.** Existing tests and expected
results were retained; no dependency was added. The rendered-component tests use
existing React, ReactDOM and esbuild packages and remove their own temporary
bundle after loading it.

The initial new rendering-test harness failed before assertions because its ESM
bundle could not execute Lucide's CommonJS React import. The harness was corrected
to emit CommonJS; no assertions or expected results were weakened. The subsequent
full test/build runs passed, including all five required Home progress states and
an additional other-page header regression check.

## Browser walkthrough

Used a separate localhost:18088 preview and a temporary synthetic SQLite file.
Created only one fictional Grade 10 explorer, **Nova Single Trail**, there.
The normal localhost:8000 application was opened read-only for final review.

| State checked | Hero behavior | Single Trail CTA |
| --- | --- | --- |
| No explorer | First-discovery welcome and nickname/grade fields; no invented metadata | Start My First Quest, disabled until setup is valid |
| New saved explorer | Fresh-adventure message; backend Grade 10 and genuine 0 points | Start My First Quest |
| Partial quests, after reload | Saved greeting, 1 of 3 quests, backend 20 points | Continue Quest 2 |
| Quests complete, initial review | Completed-discovery message; 60 points; no instruction to start quests again | Review My Explorer Profile |
| Confirmed profile | Profile-confirmed motivational message; 70 points | Explore Career Worlds |
| Saved roadmap | Saved-roadmap message; 70 points; completed Plan remains revisitable while Explore is recommended | Explore Career Worlds |
| Profile edit/reconfirmation | Updated-profile review message; saved discoveries retained; 70 points | Review My Explorer Profile |

For every normal Home state above, browser DOM checks measured **zero hero
navigation controls and exactly one prominent Trail CTA**. After an explorer was
saved, Switch Explorer appeared exactly once in the header and nowhere in the
hero. It opened the existing explorer selection/creation page with Enter.

Filled the first-time hero setup fields, confirmed fictional data, and pressed
Enter on the Trail CTA. The button was associated with `welcome-explorer-setup`
and created the explorer/opened the actual Quest 1. After saving Quest 1 and
reloading Home, the only primary action resumed the actual Quest 2. Completed the
remaining quests, confirmed the profile and explicitly saved a roadmap using the
existing pages. No static "Start with three short discovery quests" instruction
appeared after discovery completion.

Reopened profile editing and reloaded Home. The hero correctly explained review
rather than claiming the profile was confirmed. Direct exploration, roadmap
proposal and roadmap save POSTs each returned HTTP 409. The complete API state
was unchanged by blocked calls. A separate SQLite read confirmed that the shown
Grade 10 and 70 earned points matched the temporary backend record. Saved roadmap
history and the existing confirmation gate were preserved.

## Responsive/accessibility checks

Test-only frames rendered the real app at exact CSS viewport widths, avoiding
browser zoom rounding. Each used the real compiled UI and saved API response.

| Viewport | Document scroll width | Hero controls | Trail primary CTAs | Title |
| --- | --- | --- | --- | --- |
| 375px | 375px | 0 | 1 | 28px |
| 768px | 768px | 0 | 1 | 36px |
| 1280px | 1280px | 0 | 1 | 36px |

No horizontal overflow was measured. Header Switch Explorer remains visible on
mobile, while its secondary slogan is hidden. Supporting metadata is readable
and the existing reduced-motion styles remain. Native form validation, labeled
fields, keyboard submission, named header controls, semantic saved-metadata list
and existing destination-heading focus behavior were retained/exercised. Full
screen-reader speech, OS reduced-motion activation and a new outage simulation
were not performed for this increment. Final successful-view browser console
error/warning readback was empty. Viewport overrides were reset after testing.

Evidence:

- [Finished normal application](test-evidence/home-single-cta-live.jpg)
- [Observed progress-state/CTA counts](test-evidence/home-single-cta-states.json)
- [Exact viewport measurements](test-evidence/home-single-cta-responsive.json)
- [Backend grade/points and confirmation-gate checks](test-evidence/home-single-cta-api.json)

The temporary preview was stopped after verification. No live model request or
live research was needed. No new work on other pages is claimed. Stopped after
this Adventure Home navigation refinement.
