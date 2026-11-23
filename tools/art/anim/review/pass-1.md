# Pass 1 — partial render review and fixes for pass 2

The lead rendered Spearman and Horseman outside the sandbox. Spearman packed at
192,634 bytes; Horseman failed at 239,582 bytes at the old quality floor of 30.
Field Cannon, Spartan Hoplite and browser capture did not run. This is a critique
of those available outputs, not a completed four-unit visual/performance pass.
The old setup-only note is now `pass-0-setup.md` in both review directories.

## What the outputs show

- Spearman keeps the bronze kit, red crest and sunburst shield. The thrust and
  falling silhouette read clearly. Idle and move differ too little. The stone
  disc is completely absent, leaving feet floating on both backdrops.
- Horseman keeps the white rider, brown horse, tack and upright spear, but also
  lacks the stone. Its trot is more legible than the infantry shuffle. The fall
  reads as a compressed relief tipping over; it still needs a weight/contact
  judgment after the base returns. It is not approved as finished animation.
- The apparent half-height figure is a comparison-sheet bug: the old sheet
  placed a 256 px source beside 100 px render thumbnails. At native size the
  Spearman painting spans y=12..243; the baseless render spans y=11..222. The
  figure itself already has the painting's scale. Enlarging the camera projection
  would crop the spear, rather than fix the comparison. See the equal-size PNGs
  beside this note (source / original render / quality-70 repack).
- There is no rendered evidence for the other two units, and no `metrics.json`.
  300/600-token average and p95 are **not measured**.

## Changes

1. **Restore the stone and complete figure.** The camera sat at y=-1000 with its
   default far plane at 1000; the base at y=15 was beyond that plane, and body
   relief at y≈1 was partly clipped. Far distance is now 2000, with the same
   256-unit orthographic scale and 256 px cell. The stone is unskinned and has no
   animation. Its top is a continuous cream reconstruction; its unobstructed
   front rim is copied from the painting with a short blend. Copying around foot
   cutouts was inspected and rejected because it produced patches and retained
   sole/wheel fragments. Final prepared base textures were visually inspected.
2. **Improve motion without discarding the successful strike/fall.** Infantry
   stride increases from 5° to 12°, with 5 px alternating foot lift; horse stride
   increases from 9° to 13°. A twice-per-cycle body bob carries the spear. Idle
   doubles the small breath and adds a gentle lateral shift. Attack/death angles
   remain; independent attack translations of spear/shield were removed so their
   pivots stay on their parent grip points. CPU checks assert this at every pose.
   Larger motion can expose seams; the new renders must establish visual contact.
3. **Control coverage and budget.** Transparent materials use hashed coverage;
   Eevee samples increase from 16 to 64. Packing clears hidden RGB and quantizes
   alpha to 32 coverage levels (maximum alpha error 4/255), retaining soft edges.
   Method 6 probes quality 80/70/60 and refuses anything below 60 or above
   200,000 bytes. Profiles retain 40, 34, 27 or finally 23 frames. All but the last
   retain eight move frames; attack always retains anticipation, first strike,
   peak and recovery, and death retains two settled poses. FPS preserves overall
   clip duration, though reduced nonuniform samples change within-clip timing.
   The last four-frame move fallback needs particular cadence review if selected.
   No atlas dimensions, cell size, anchors or JSON fields changed.
4. **Make review honest.** Source and frame sheets now use equal 256 px cells;
   the gallery's source and inspection canvases display at 256 px. Frame counts,
   FPS and capture selections follow metadata. Capture asserts native inspection
   size. `pass.sh` archives each completed unit's sheet, previews and packing
   report into `review/pass-N/`, preserving partial-pass evidence. The packer
   probes in memory and never leaves an oversized failed atlas as delivery.
5. **Catch this failure next time.** CPU rig audits check camera depth as well as
   projected bounds and fixed grip pivots. Atlas validation checks the exposed
   stationary front rim and neutral framing against the source, in addition to
   metadata, size, alpha, transparent padding and the held death pose.

## Measured sandbox results

Repacked the existing pass-1 PNGs into `review/pass-1-repack/`, not into shipped
assets. These remain the old baseless poses; they are not pass-2 renders.

| Unit | Repacked bytes | Quality | Packed frames | Result |
| --- | ---: | ---: | ---: | --- |
| Spearman | 177,598 | 70 | 40 (8/8/10/4/10) | Contract validation passed |
| Horseman | 195,520 | 70 | 34 (4/8/10/4/8) | Contract validation passed |
| Field Cannon | — | — | — | No rendered frames available |
| Spartan Hoplite | — | — | — | No rendered frames available |

Pack reports record every attempted size/quality and selected source index.
Full visual validation correctly rejects the old Spearman at idle frame 0 with
`missing/moving stone rim`. The original partial app atlases are left untracked,
unchanged, and excluded from this commit. `pass.sh 2` will replace them.

- `venv/bin/python tools/art/anim/test_pipeline.py`: **5 tests passed**, including
  all four contracts/160 synthetic frames, coverage error, timing and key poses,
  budget fallback, failed-pack preservation, and missing-stone regression.
- `build.sh <slug> 2 --model-only` and `--audit-only`: **all four passed**, 160
  poses total. Final masters contain the revised textures/rigs. No rendering.
- Python compilation, `node --check` for gallery/capture, `bash -n` for build/pass,
  and `git diff --check`: **passed**.
- `python3 tools/gates/check.py HEAD --base origin/master --checks-only --skip art`:
  **exit 1**. `public-claims: PASS`; hygiene flagged the pre-existing unspaced
  Python matrix expression `bone.matrix @ bone.bone.matrix_local` as an email.
  Added spaces around `@` in the working file. Direct hygiene line checks over
  all 16 animation/skill text files then passed with **0 findings**. This is not
  a replacement for the full gate: `check.py` reads committed git objects.
  Browser art checks were skipped as required by the no-Chromium boundary.
- After making the rim test ignore antialiased boundary pixels, reran the focused
  four-unit contract/missing-base integration test: **1 test passed**.
- Blender logged nonfatal sandbox thumbnail-write and `nice` permission warnings;
  models saved and audits exited 0. No Metal, Chromium, AWS or cloud attempt made.

## Expected effect and lead handoff

| Unit | Expected pass-2 effect | Inspect especially |
| --- | --- | --- |
| Spearman | Stone returns at original scale; distinct breathing/marching; thrust/fall retained | Shield rim, wrist/spear grip, knee/hip seams, planted disc |
| Horseman | Stone returns; clearer trot; bounded atlas at quality ≥60 | Hoof contact, rider/spear attachment, relief-like fall, selected packing profile |
| Field Cannon | Stone and previously clipped body restored; common budget policy | First rendered wheel occlusion/rotation, crew hands, smoke, top/rim consistency |
| Spartan Hoplite | Stone returns; stronger march and breath; unchanged thrust/fall angles | First rendered lambda shield, long spear bounds/grip and cloak seams |

Run **`tools/art/anim/pass.sh 2` on the host from this worktree**, with the same
working Blender/Playwright environment used for pass 1. No extra command or cloud
setup is needed. It still renders 40 poses per unit before selecting packed
frames. Inspect all sheets and decoded gallery captures and read the per-unit
`*-pack.json` reports. Restoring the base changes entropy, so the measured pass-1
repack sizes are not forecasts of final bytes. The packer enforces the budget for
all units but new Cannon/Hoplite sizes cannot be measured until they render.
If even the minimum profile exceeds the budget it stops without publishing an
oversized asset; do not lower the floor. Review then continues in the next round.

No pass-2 visual quality or performance approval is claimed. The relief method's
hidden-surface limitations remain, and Claude art review is still owed before
merge. No rules or app runtime files changed; no full Rust/app build was needed.

## Commit handoff

`git add` and `git commit` both failed with exit 128: the sandbox denied creating
`.git/worktrees/lane-1/index.lock`. Per the task, changes are left uncommitted for
the runner; no alternate index, permission workaround, push or merge was tried.
`origin/master` is already an ancestor of HEAD (2 ahead / 0 behind), so no merge
was needed. Stage `tools/art/anim` and `.claude/skills/legatum-art/SKILL.md`, **not**
the pre-existing untracked `app/src/assets/units/anim/` pass-1 artifacts. Re-run
the static gate after the runner commits so it sees the fixed matrix expression.

Suggested commit:

```text
Fix animated unit bases, motion and atlas budget after pass 1

Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>
```
