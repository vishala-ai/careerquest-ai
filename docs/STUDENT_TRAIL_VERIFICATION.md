# Student Journey — Adventure Trail redesign

The hero's duplicate next-action button was subsequently removed; the Trail is
now the single primary journey controller. See the current
[Home navigation refinement report](HOME_NAVIGATION_REFINEMENT.md). The connected
trail design and persisted-state behavior described below remain in place.

Scope: **Student Journey only**. The welcome hero markup, hero illustration,
branding, navigation, hero CTA selection, profile setup, API, database schema,
LangGraph workflow, Streamlit fallback and other pages were preserved.
`AGENTS.md`, the current Welcome implementation, persisted-state domain service,
existing tests and the prior Welcome screenshots/report were inspected first.

## Changed files

- `frontend/src/pages/Welcome.jsx`: imports the trail component and replaces only
  the former Student Journey card section. Hero markup and its event handlers
  are unchanged. Removed the old section's unused icon imports.
- `frontend/src/components/StudentTrail.jsx`: new reusable trail with large
  milestone icons, a curved SVG connection, decorative leaf/star/flag artwork,
  status text, one prominent recommended CTA, accessible milestone controls,
  prerequisites and historical-completion labels.
- `frontend/src/components/student-trail.css`: component-scoped purple/teal
  design, alternating desktop milestones, vertical mobile/tablet stepper,
  focus rings, restrained hover effects and reduced-motion rules.
- `frontend/src/studentTrail.js`: read-only presentation projection of the
  existing `welcomeJourney` result. Recommendation never changes availability
  or erases completion. The hero's domain service is unchanged.
- `frontend/tests/student-trail.test.js`: six new regression tests covering the
  requested persisted-state scenarios and retained hero action/page targets.
- This report, a link from the prior report and `student-trail-*` evidence.

States use both visual styling and explicit text: **Completed**, **Recommended
Next**, **Available** and **Locked**. A recommended milestone is labeled **Your
Next Adventure**. Plan and Reflect can be available before Explore is completed;
completed Plan/Reflect remain actionable when Explore is recommended again.
There is no sequence-position lock. Genuine prerequisites are explorer creation,
quest completion before profile review, and current profile confirmation before
personalized work. After a profile edit, saved history remains labeled
"Previously completed" while the existing confirmation gate blocks new
personalized activity until reconfirmation.

## Commands and automated results

Executed from the project root:

```sh
.venv/bin/python -m unittest discover -s tests -v
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend test
PATH=/private/tmp/careerquest-node-runtime/node-v22.15.0-darwin-arm64/bin:$PATH npm --prefix frontend run build
```

**35 backend tests passed; 26 frontend tests passed; React production build
passed. Zero automated failures or skips.** Existing test expectations were not
changed. No dependencies were added. Backend allowlist, failure handling,
confirmation gates, persistence and reward-integrity tests remain passing.

## Browser walkthrough

Used one new fictional Grade 11 explorer, **Orbit Trail Demo**, on localhost:18086
with a separate temporary synthetic SQLite file. No existing database was reset
or modified. A temporary wrapper outside application source served the real
compiled app and existing API, plus viewport and CSS-motion verification fixtures.

1. New visitor: no completed stages; prerequisite text was visible; the recommended
   setup link focused the existing hero nickname input. Submitted synthetic
   nickname/grade through the unchanged Welcome setup and opened Quest 1.
2. Partial quests: completed Quest 1 and reloaded Welcome. Discover remained
   Recommended Next with 1 of 3 saved quests. The trail CTA opened Quest 2.
3. Completed remaining quests: Discover became Completed and Confirm became
   Recommended Next. The trail CTA opened the actual Explorer Profile review.
4. Confirmed profile: Explore became Recommended Next; Plan and Reflect both
   showed Available. Enter on the Plan milestone opened the real roadmap page
   without forcing career exploration first. Explicitly saved the proposal.
5. Enter on the available Reflect milestone opened the real reflection form.
   Saved one fictional reflection. On reload, Explore remained recommended,
   while Plan and Reflect showed Completed and both milestone controls stayed
   enabled. Revisit Plan and Revisit Reflect opened their correct pages.
6. Opened profile editing through Revisit Confirm. After returning/reloading,
   Confirm became recommended; personalized stages showed the genuine
   confirmation prerequisite and saved Plan/Reflect history remained visible.
   Direct exploration/proposal/save/reflection POSTs returned HTTP 409. The
   complete API state compared equal before and after blocked requests: three
   quests, saved roadmap version 1, one reflection and **80 XP** were retained.
7. Reconfirmed the unchanged draft. Explore became recommended again and saved
   Plan/Reflect controls were enabled. The original hero CTA still read Explore
   Career Worlds. Existing unique-XP tests also passed; this trail performs no
   writes itself.
8. The normal localhost:8000 app independently displayed a returning fictional
   explorer with all stages previously completed. Explore was recommended again,
   and saved Plan/Reflect remained Completed and enabled. No write action was
   performed in that normal database. The finished normal app is left open.

## Responsive and accessibility checks

The real app was embedded in test-only frames with **exact CSS viewport widths**
of 375px, 768px and 1280px. This avoids the selected browser's 80% zoom rounding
without changing the user's browser or OS settings. These were real app frames
using persisted API data, not screenshots or mocked UI states.

| App viewport | Document scroll width | Layout | Stage titles | Descriptions |
| --- | --- | --- | --- | --- |
| 375px | 375px | Vertical stepper | 20px | 17px |
| 768px | 768px | Vertical stepper | 22px | 17px |
| 1280px | 1280px | Curved horizontal trail | 22px | 17px |

No horizontal overflow was measured. All mobile/tablet node centers shared the
same horizontal coordinate; desktop nodes alternated vertically along the curve.

Keyboard Enter activated setup, recommended and available milestone navigation.
Tab reached completed-step revisit controls with a visible focus outline. The
accessibility tree exposed an ordered five-step list, descriptive button names,
current-step state, status text, linked descriptions and native disabled states.
Exactly one current milestone and one prominent trail CTA were present. The
setup link focused the nickname input. Decorative SVGs/icons are hidden from
assistive technology. Actual screen-reader speech was not tested.

Reduced-motion CSS behavior was exercised through **isolated stylesheet media
condition emulation**, not by changing the OS preference. The temporary preview
mapped the reduced-motion branch to an always-matching media condition and the
no-preference branch to a nonmatching condition, leaving production files
unchanged. In the actual rendered app, node transition duration changed from
0.16s to **0s**, animation name was **none**, and decorative leaf/flag transforms
were **none**. Normal styling was restored afterward. Native OS/browser
reduced-motion activation remains an unperformed manual check.

Five principal text/background pairs were calculated at **5.44:1–8.46:1**,
exceeding 4.5:1 for normal text. This is not a complete assistive-technology or
contrast audit. Final successful-page console error/warning readback was empty.
Temporary viewport overrides were reset and the verification server was stopped.

## Evidence

- [Finished trail in the existing application](test-evidence/student-trail-live-desktop.jpg)
- [New student](test-evidence/student-trail-new.jpg)
- [Confirmed profile with available Plan/Reflect](test-evidence/student-trail-available.jpg)
- [375px vertical stepper and keyboard focus](test-evidence/student-trail-mobile-stepper.jpg)
- [768px real-app frame](test-evidence/student-trail-768.jpg)
- [1280px real-app frame](test-evidence/student-trail-1280.jpg)
- [Reconfirmation and preserved history](test-evidence/student-trail-reconfirmation.jpg)
- [Exact viewport/typography measurements](test-evidence/student-trail-responsive.json)
- [Reduced-motion branch results](test-evidence/student-trail-reduced-motion.json)
- [Confirmation-gate and state-preservation results](test-evidence/student-trail-api.json)
- [Contrast calculations](test-evidence/student-trail-contrast.json)

No live model or live research request was used. Retrieval remains curated and
offline. No completion celebration animation was added; hover motion is optional
and suppressed by reduced-motion rules. No other page's pending specification
work is claimed complete. Stopped after the Student Journey redesign.
