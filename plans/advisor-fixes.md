# Advisor review fixes (PR #102) — working list, delete this file in the last commit

Branch `claude/project-thread-k9y1sh` on GitHub `samcorcos/legatum`. Read `app/src/ui/advisorModel.ts`, `Advisor.tsx`, `Advisor.css`, `advisor.test.ts`, `app/e2e/tour/first-run-advisor.spec.ts`, and `.claude/skills/legatum-ui/SKILL.md` (plain language + glossary) first. Four reviewers found the issues below; fix all of them, with tests.

## Blockers
1. **Placement inside dialogs.** The card is portalled into `dialog.tech-modal` at the top-centre slot and covers "Queue all 5, cheapest first" (1440x900) and the technology names (1000x600). Inside a dialog, show the advisor as a **compact one-line strip docked at the dialog's bottom edge** (title-less: "Advisor · Click Research now on Writing. Writing unlocks the Lyceum: +6 Science in a city.  Not now · Turn off"), never over cards, titles or buttons. While the advisor rings a card's button, render the dialog's "Queue all … cheapest first" as a secondary (outline) button so there is one primary.
2. **Hidden during hand-off and overlays.** Add `s.handoff !== null` to `paused` in `Advisor.tsx`, and also hide whenever a non-dismissible game overlay is up (`[data-game-overlay]:not([data-dismissible])`, re-checked on store changes; alarm screen, free technologies, war interstitials). Unit test: no card while `handoff` is set.
3. **Never silent while a unit needs orders.** When `unitSuggestion` returns null (Hard issued SetAutoFire, UpgradeUnit, AirStrike, Rebase, Action, DisbandUnit, …), fall back to the generic suggestion for that unit (`unitSuggestion(ctx, unit, undefined)`). Test with a plan holding `SetAutoFire` and `UpgradeUnit`.
4. **Follow the turn's decision order.** If a pending decision of a kind the advisor doesn't handle (siege, diplomacy, freeTechs, goal, air, treasury) comes before the first handled one, show a card "Answer this first" whose why is that decision's own label and whose one step is "Click {the dock button's label}" ringing the turn control (`.seatbar .cta` / phone dock). Test it.
5. **Card never covers its own target or the selection (1000x600).** The camera centres the capital under the top-centre card. When the ring's rect, or the selected unit's/city's tile (via `tileOnScreen`), intersects the card, move the card to a free slot: bottom-centre above the Lens chip (clear of the left dock, right sidebar and the turn button). Never pan the camera. Tour assertion: the card never intersects the ring or the selected tile.
6. **Stale e2e:** `app/e2e/guide.spec.ts` lines ~66-104 still test the removed hints (`first-game-hint`, "Reset hints", "First-game hints" label). Rewrite for the advisor's settings switch. Fix stale "first-game hint" comments in `resources.spec.ts`, `search-timing.spec.ts`, `diplomacy.spec.ts`.

## Majors
7. **Animations setting.** The ring must also be still when the in-game Animations switch is off (see how `celebrate/ScoreCheck.tsx` or `MomentLane` read `animationsOn`/`motionStill`), not only under `prefers-reduced-motion`.
8. **Reasons (plain language), in `advisorWhy`:**
   - Settler: "A Settler founds a new city, and more cities grow your empire."
   - Military unit, enemies near: "Enemy units are near {City}. A military unit can defend it."; otherwise state a computed fact: "You have {n} military unit(s) for {m} city/cities." (check both one and many forms; 0 → "You have no military units guarding {City}.").
   - Building: use only Food, Production, Gold or Science yield names (map the yield key explicitly), e.g. "Granary adds 2 Food in {City}."; if no yield, "{Building} helps {City}." (never "strengthens").
   - Research: "{Tech} unlocks the {Thing}." and add its main effect if a helper gives one (e.g. "Writing unlocks the Lyceum: +6 Science in a city."). Keep one fallback "Research gives your empire new choices." (single constant).
   - Final fallback: "This is your best move right now."
   - Fortify: keep "Fortified units defend better and heal." (true: the Guide says Fortify heals and strengthens defences).
   - "Move toward {City}." → "Move closer to {City}." is fine; prefer a purpose if known.
9. **Instructions name the exact control label:** research step 2 "Click Research now on {Tech}."; ranged "Click Ranged Attack." (exact label from `UnitPanel.tsx`); every Click becomes Tap on touch (`ctx.touch`), including Fortify/Wait, Found City, Auto-explore, Ranged, End turn. The no-plan unit step: "Click Fortify, or move it, or press Space to skip." ringing Fortify.
10. **Tests** (jsdom, `@testing-library/react`): mount `UnitPanel` / `CityPanel` (see existing `UnitPanel.test.tsx`, `CityPanel.test.tsx` for fixtures) and assert `targetElement` (export it) finds Found City, Fortify/Wait, Auto-explore, Ranged Attack, Build on X; the off switch (`setEnabled(false)` hides the card); "Not now" moves on; pauses (scenario, busy, ready, handoff).

## Minors / polish
11. Hide "Step 1 of 1" when a suggestion has one step.
12. Welcome card: no duplicate eyebrow/title — title "Your advisor will guide you", why "I'll suggest what to do each turn and show you where to click." Make Continue answer Return while the welcome card shows, and step the dock's Return chip back per the "One Return on screen" rule if that mechanism exists (`returnOwned` in `SeatBar.tsx`).
13. Faction emblem beside the "Advisor" label (reuse the existing faction emblem component used in the top bar or faction sheets), a small premium touch until painted advisor portraits arrive.
14. Settings: label "Show the advisor", foot "On by default. Turn it off any time."
15. Race lesson title "Win the victory race".
16. Guide (`GuideContent.tsx`) advisor paragraph: "shows where to click" instead of "points to its control", and add: "It never gives orders for you: you make each move yourself. Its advice is what a strong AI empire would do with what you can see. Not now moves to the next decision; turn it off in Settings or the Menu."
17. Map ring: a hexagon outline (clip-path or SVG hex sized to the tile radius) instead of a circle, same pulse.
18. Phone width: stack the card above the city panel's header instead of covering it (push `--story-top`).
19. Tour (`first-run-advisor.spec.ts`): don't shoot two identical screens (skip 03 when step 2 already showed at 02); assert the card never intersects the ring, the selected tile, any `.btn.primary` or `.era-card` title inside an open dialog.

## Then
- `cd app && npx tsc -b && npx vitest run src/ui src/celtsBarbarians.test.ts` and the gates test `python3 tools/gates/test_check_reviews.py`; `cargo fmt --check` if Rust touched.
- If Playwright can run, run `npx playwright test e2e/tour/first-run-advisor e2e/guide --trace off` (needs `LEGATUM_RELAY_URL=http://127.0.0.1:8787 scripts/build-web.sh`); if the sandbox blocks the browser, say so — the lead runs it in the cloud.
- Learnings: one new file `docs/learnings/2026-11/22-advisor-placement.md` only if something non-obvious came up. Never append to a month file.
- Update `.claude/skills/legatum-ui/SKILL.md` advisor line with: a floating advisor card never covers its target, the selection, a dialog's primary or the options' names; inside a dialog it is a one-line strip; looping animations honour the Animations switch.
- Delete this file in the last commit. Commit in logical commits; push the branch (never master); no PR changes.
