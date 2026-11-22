# In-game advisor: implementation spec

Repo: GitHub `samcorcos/legatum`, branch `claude/project-thread-k9y1sh` (cut from master; its first commit holds the work in progress below — build on it). This file is a working plan for the branch and is deleted before merge.
Read first: `CLAUDE.md`, `.claude/skills/legatum-ui/SKILL.md` (esp. "Game text: plain language" + glossary, pillar 9), `.claude/skills/legatum-rules/SKILL.md`.

## What Sam wants (owner, 2026-11-22)
His wife (a non-gamer) couldn't find right-click to move, founding cities, or picking research. He wants an **advisor that is on by default** (switch off in Settings / Menu), so the first game *is* the tutorial:
- It recommends **what the Hard AI would do for her seat this turn** and explains **why** in one plain sentence.
- **Explain only — no "Do it" button.** She must learn the commands. Each suggestion is a sequence of *exact* instructions ("Click your Spearman", then "Right-click this tile"), each with a **big pulsing highlight on the exact unit / tile / UI control** to use. Use gilt (`var(--gilt)`), not red (red = cost/danger in this game). Respect `prefers-reduced-motion` (static ring).
- The UI must stay uncluttered: one compact advisor card + the ring. Nothing else.

## Already done (by me)
1. Engine hook `crates/wasm/src/lib.rs::advisor_orders(view_json) -> orders JSON` (Hard brain planning from the seat's own fogged view, cached per seat per turn). Rebuild the WASM package so TS can call it (look at `scripts/build-web.sh` / how `app/src/wasm-pkg` is produced; `npx tsc -b` currently fails only because wasm-pkg is missing). Add a TS wrapper next to `cityAutomationPreview` in `app/src/automation.ts` style: `advisorOrders(view): Order[] | null`, using `loadedWasmModule()`, cached per `PlayerView` object (WeakMap), try/catch → null. Add a Rust unit test for `advisor_orders_json` (turn-1 standard game view returns non-empty orders including a SetProduction and SetResearch*) where the other `*_json` fns are tested.
2. `app/src/map/screenPos.ts::tileOnScreen(hex)` → viewport `{x, y, radius}` registered by MapCanvas. Use it for the map ring (a fixed DOM div repositioned every animation frame while a map target is shown; pointer-events: none).
3. Draft `app/src/ui/tutorial.ts` + `app/src/ui/Tutorial.tsx` + `Tutorial.css` (an action-gated basics tutorial that replaced `FirstGameHints`/`hintState`; wired into GameScreen, TitleScreen settings, GameMenu). **Rework these into the advisor** (rename to `advisor.ts`, `Advisor.tsx`, `Advisor.css`; settings component `AdvisorSettings`, label "Advisor", foot status "Shown until you turn it off", button none or "Restart lessons"). Keep: the storage key `legatum.first-game-hints.v2` and honouring `enabled: false` (108 e2e specs disable it that way), the pause conditions, the `--hint-bottom` layout effect, `data-overlay-slot="story-hint"`, the `.tutorial-card`→ rename class to `.advisor-card` and update `map/MapCanvas.tsx`, `map/lenses.css`, `touch.css` refs.

## Advisor behaviour
Pure logic in `app/src/ui/advisor.ts` (unit-tested with `FixtureClient` like the old `hintState.test.ts` did — see git history `git show HEAD:app/src/ui/hintState.test.ts`), component in `Advisor.tsx`.

The advisor shows **one suggestion at a time**, following the turn's own decision order (`pendingDecisions` in `app/src/turnFlow.ts`; on turn 1: capital's build, units, research). For each pending decision it takes the Hard plan's order for that thing:
- City build (`SetProduction`/`SetProductionQueue` for that city): steps: 1 "Click {City}" [ring on city tile] → 2 "Click Build on {Item}" [ring on that build card's Build button inside `.city-panel`] → done when the player's orders set that city's production (to anything: if she picks something else, she decided; move on).
- Research (`SetResearch`/`SetResearchQueue`): 1 "Click Research at the top" (or "press T") [ring on `.topbar .research-chip`] → 2 "Click {Tech}" [ring on that tech card in `dialog.tech-modal`] → done when research queue non-empty.
- Unit move (`MoveUnit`/`MoveUnitPath` to a tile): 1 "Click your {Unit}" [ring on unit tile] → 2 mouse: "Right-click the marked tile. On a trackpad, click with two fingers." / touch: "Tap the marked tile, then tap it again." [ring on destination tile] → done when that unit has any order.
- Attack (move/RangedAttack onto an enemy): same, step 2 "Right-click the {enemy unit/city}" (ranged: "Click Ranged attack, or press R, then click the target"). Why includes the battle forecast if available (`client.forecast` as MapCanvas uses it) — e.g. "You should win: about 80% chance." Never invent numbers.
- Fortify/Sleep/Skip: step 2 "Click Fortify, or press F" [ring on that button in the unit card] / "Press Space to skip this turn".
- Auto-explore (`SetAutomation Explore`): "Click Explore, or press E".
- Found city (`FoundCity`): "Click Found City, or press B" [ring on the button].
- Other orders (diplomacy, purchases, upgrades, goals…): skip them for now (no suggestion), unless trivial.
- When every decision is made: "End the turn": "Click End turn, or press Return" [ring on `.seatbar .cta` / phone `.phone-turn-dock`]. In multiplayer say Ready.
- After she ends turn 1: a one-time lesson "The Turn report lists battles, discoveries and failed orders. Press L to open it." (acknowledge). And a one-time "Win the race for VP" lesson pointing at the Victory race (`.game .panel.vp`), around turn 8. Reuse the drafted copy in `tutorial.ts` where it fits; these one-time lessons are remembered in storage like the old `seen` list.
- First turn only: a welcome card "Your advisor" with one line on what it does and two buttons: "Continue" (primary) and "Turn off advisor".
- Every card has a quiet "Turn off advisor" link (and Esc does nothing destructive). Skipping a single suggestion: "Not now" moves to the next decision for this turn.
- If the WASM plan is unavailable (not loaded / threw), fall back to the basics wording without a specific recommendation (e.g. "Click your capital and pick something to build.").

### The "why" (one plain sentence, built in TS from the view; never a code term)
Write a small `advisorWhy(order, view, ...)` with honest, specific reasons, e.g.:
- Settler: "{City} has population {n}: a Settler founds a new city, and more cities mean a bigger empire."
- Military unit while a rival/barbarian military unit is within 6 tiles of the city: "{n} enemy units are within {d} tiles of {City}."; otherwise "Your army is small for {n} cities."
- Building: its main effect from data (`buildingStatsFor`/existing description text), e.g. "Granary: +2 Food, so {City} grows faster."
- Research: what it unlocks for this faction (reuse existing tech unlock text helpers in `ui/TechDetail.tsx`/`techCardUnlocks`).
- Move Settler: "This is a good place for a city." (+ settle-site yields if a helper exists, `map/settleAdvice.ts`).
- Move Scout / explore: "Exploring finds city sites, ruins and rivals."
- Move military toward own city: "Guard {City}: enemy units are near."; toward enemy: "Join the attack on {target}."; otherwise "Move toward {nearest own city name, relative}".
- Fortify: "Fortified units defend better and heal."
Keep every sentence ≤ ~20 words, second person, British spelling, glossary terms (tile, population, Food/Production…, VP, city HP, at Peace / at War). Text for player only.

## UI
- One card, the existing story-hint slot (top centre, under the top bar, `.advisor-card`), ~340px wide, gilt top rule: small "Advisor" label is fine (it names the speaker; it's not a tagline), title = the recommendation ("Build a Settler in Athens"), the why in muted ink, then the current instruction as a numbered step line in bold ink with a key chip (`Kbd` from `./index`) where there is a key, and the step count "Step 1 of 2". Actions row: "Not now" + "Turn off advisor" (quiet links). No Do it.
- Ring: `.advisor-ring` fixed, z above map/panels, pointer-events none, 2–3px gilt border + outer glow pulse (1.4s), radius = tile radius*1.1 for map targets, element rect+6px for controls. Only one ring at a time (the current step's target). If the target control is not on screen (e.g. panel not open), ring the control that opens it instead, or hide the ring — never ring a stale position.
- Must fit and not cover the turn's primary button at 1000x600 and 1440x900, and work on phone width (story slot rules in `touch.css`).
- Must not show during scenarios, celebrations, dialogs, guide (keep the existing pause list).

## Also update
- `app/e2e/tour/first-run-hints.spec.ts` → rename `first-run-advisor.spec.ts`, shoots: welcome, build suggestion with ring on city then on Build button, research with ring, a unit move with ring on destination, end turn. Keep its "never covers the primary button" check. Run it at both sizes (see `app/playwright.config.ts`; the tour needs a web build — check `scripts/build-web.sh`). Look at every screenshot yourself and fix what looks wrong.
- Guide (`app/src/ui/GuideContent.tsx`): one short paragraph in 'turns' about the advisor (on by default; turn off in Settings or the Menu) and in 'controls' nothing new unless needed.
- `.claude/skills/legatum-rules/references/` (whichever file covers UI/turn flow helpers — check `index.md`) and `legatum-ui` SKILL.md: one line each on the advisor's rules (recommends Hard's plan from the seat's own view, explain only, one card + one ring).
- `docs/learnings/2026-11.md`: dated entry if you learn something non-obvious.
- Tests: vitest for advisor logic (decision order, done-when-ordered-anything, fallback without WASM, Celts don't treat barbarians as enemies — keep `celtsBarbarians.test.ts` passing, copy lint `ui/copySource.test.ts`/`textArtifacts.test.tsx` passing). Run `cd app && npx tsc -b && npx vitest run` (full vitest is OK once at the end; re-run only failing files while fixing). `cargo test -p legatum-wasm` for the Rust test. `cargo clippy -p legatum-wasm -- -D warnings` and `cargo fmt`.

## Don'ts
- Commit in logical commits on `claude/project-thread-k9y1sh` and push that branch to `samcorcos/legatum` (never to master, never another remote). Don't open a PR.
- Don't touch `tools/gates/`, `.claude/agents/`, `CLAUDE.md` or `.github/` (the lead edits those in parallel).
- No new dependencies. No save-format or core rules change (the advisor is client-only plus the stateless WASM fn).
- Report back: files changed, test results, screenshot paths, anything you couldn't do.
