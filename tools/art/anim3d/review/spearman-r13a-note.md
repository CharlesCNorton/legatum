Files changed relative to round 12 (07643cd4):
- tools/art/anim3d/units/spearman/stance.py
- tools/art/anim3d/units/spearman/stance_preview.py
- tools/art/anim3d/units/spearman/stance_report.py
- tools/art/anim3d/units/spearman/frozen-actions.json
- tools/art/anim3d/PLAYBOOK.md
- tools/art/anim3d/LOG.md

# Spearman round 13a — rest stance only

Not PASS. A small, measurable stance cleanup; no claim that the remaining feet
or base gap is solved. The exact R12 source tree was applied after `git merge
astra/unit-anim-3d-v2` failed to create ORIG_HEAD.lock. The branch/index still
need the runner's merge/commit. `spearman-r13a-files.txt` lists all 43 inherited
R12 paths separately; `spearman-r13a-lane-only.patch` contains only the six lane
files above. Commit message: lanes/spearman-r13a/commit-message.txt.

## Change and measurement

Kept Fable B's rest geometry, foot dimensions, shield and helmet. Moved the
planted ankles inward by 3 mm (spear side) and 10 mm (shield side), solving
thigh/calf lengths with the old knee pole. Rest foot/ball rotation, original
calf-to-foot offset, bind, weights and geometry remain. Projection is rebuilt
once on the new guard. No walk orientation, material, camera, base or prop edit.

Matched A/B: Blender 5.3.0, Cycles CPU, 256 px, 16 samples, seed 17, no denoising
or adaptive sampling, Standard transform, one fixed R12 look calibration,
analytic-sun proxy without cast shadows, no grade. Both are fresh CPU renders;
do not compare their values directly to R12's 512-to-256 GPU IoU 0.938384.

| Measure | R12 CPU | R13a CPU |
| --- | ---: | ---: |
| Critique IoU, best ±3 px | .935824 | .936745 |
| Best offset x,y | 0,0 | 1,0 |
| Zero-offset IoU | .935824 | .936121 |
| Lower-leg IoU, box 80,180–175,216, alpha >8 | .916877 | .918687 |
| Lower-leg RGB error /255 | 24.517 | 24.330 |
| Blurred ΔE at zero offset | 4.5771 | 4.5301 |
| Legs regional blurred ΔE | 2.9283 | 2.7220 |
| Feet regional blurred ΔE | 13.3272 | 13.3246 |
| Projected bone shin lean, spear/shield, px | 10.376 / 5.304 | 9.312 / 4.470 |
| Projected ankle separation, px | 50.391 | 49.311 |

Shield regional ΔE changes 2.1732 → 2.1791 (tiny regression); head/crest is
identical at 3.8141. Whole-image and regional improvements are small. Do not
attribute the look's existing surface quality to this pose-only change.

Mesh + weight hashes, bind matrices, upper-body pose and camera/settings are
identical. Shield rows y110–169/x138–189 and helmet/crest rows y55–99/x115–149
have identical alpha spans before/after. Rest sole clearance is 1.000 mm on
both sides, within the unchanged 2 mm gate.

## Rejected probes and learning

A 15/10 mm inward shift with the old knee pole reduced the A-frame more, but
its searched IoU .936896 hid a zero-offset fall to .935024 and lower-leg fall
to .911883. At 30/20 mm, lower-leg overlap fell to .904165. A forward-only
spear-side knee pole also lost overlap (.935164 IoU at 15/10 mm). Kept the
smallest tested change that improved both fixed alignment and lower legs.

The fitted foot heads already sit 9.26/23.60 mm above calf endpoints. Solving
the calf directly to the foot head inadvertently bent the knees 6–7 cm even
for a small ankle move. Preserve that offset and translate the complete foot
and ball together. Geometry fitting and guard fitting must stay separate.

## Validation and artifacts

- 33 existing tests pass: kit 24, critique 4, pipeline 2, look 3.
- Scene check passes; all five clips rebuilt from the new master; all 40 saved
  poses audit with zero findings; no stale source hashes.
- Walk: 33 dense samples, all eight limits pass. Slip .001853 mm; planted floor
  error .000202 mm; heading 5.142°, readable heading 9.175°; seam zero; root
  correction 48.963 mm, foot IK 19.943 mm, sole translation 28.186 mm. The
  near-limit readable heading/root correction are inherited and still need
  attention if the motion lane changes the walk. No limit was loosened.
- Top/front feet sheet is actual geometry, CPU 192 px / 4 samples with the
  stored hybrid materials; its pale undersides are not the painted-look movie.
- All 40 painted CPU proxy clip frames rendered at 256 px / 8 samples; atlas
  validates at 192510 bytes, Q80, trimmed 160 cells, 8/8/10/4/10 frames. Movie:
  1600×352, H.264 yuv420p, 192 frames, 8 seconds; ffprobe verified.
- Viewed native 256/160/64 comparisons and crossfades, enlarged lower legs,
  all decoded cells, every top/front foot sample and eight movie samples.
- Idle and attack retain the source choreography code, but the guard rebase
  changes actions. The new reviewed hashes are explicit in frozen-actions.json
  and check_frozen.py passes. Do not call them identical to R12 actions.
- Python parse, Bash syntax, whitespace and import checks pass. The R12 tree
  lacks kit/check_imports.py; ran the read-only checker from lane-3 against
  this checkout (0 unresolved imports), without editing the shared kit.

Shared review outputs: spearman-r13a-compare-{256,160,64}.png,
spearman-r13a-leg-crops.png, spearman-r13a-contact-sheet.png,
spearman-r13a-feet-check.png, spearman-r13a-clips.mp4,
spearman-r13a-movie-samples.png, spearman-r13a-metrics.json and
spearman-r13a-receipt.json. Masters, clips, source receipts and preview atlas
remain isolated under lanes/spearman-r13a/. Shipped assets remain the inherited
R12 GPU versions.

## Honest visual verdict and handoff

At 256 the stance is fractionally tighter and the shins less splayed. At 160
and 64, the before/after difference is very subtle; it is still the same unit,
not yet hard to distinguish from the painting. Main remaining gaps:
1. Feet (x84–165, y206–224): too small/pale, indistinct straps and heavy sole
   edges; the stance shift does not solve the shape/value deficit.
2. Stone (x75–180, y215–244): flatter/oranger than the painting, weak bright lip
   and missing faint shadow in this CPU proxy. Surface lane owns this.
3. Existing motion tells: raised trailing foot and shaft crossing the kneeling
   figure. Clips remain readable; this lane does not alter their choreography.

No PASS file. The complete executable GPU entry is unchanged:
`ROUND=13 tools/art/anim3d/units/spearman/gpu.sh`.
It rebuilds look calibration and every clip, renders all stages and 512/256
masters, packs/validates 160 cells, checks feet and writes the round movie.
The lead must confirm the marginal stance gain on GPU. If other lanes alter
the merged guard/choreography, review that combined build before re-pinning
its idle/attack action receipt; do not bypass check_frozen.py.

FOCUS a: Small measured stance cleanup; verify the GPU comparison before keeping it.
FOCUS b: Sandal/base values and contact shadows remain the assigned surface work.
FOCUS c: Existing walk/death refinements remain the assigned motion work.
