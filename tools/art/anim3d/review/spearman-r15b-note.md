# Spearman round 15b — selected walk finish; rest-shadow choice remains open

Files changed relative to round 14:
- tools/art/anim3d/PLAYBOOK.md
- tools/art/anim3d/units/spearman/look.py
- tools/art/anim3d/units/spearman/look_receipt.py
- tools/art/anim3d/units/spearman/gpu.sh
- tools/art/anim3d/units/spearman/foot_finish.py
- tools/art/anim3d/units/spearman/foot_finish_review.py
- tools/art/anim3d/units/spearman/foot_finish_report.py

The complete 24-file imported R14 baseline is listed separately in
`spearman-r15b-files.json`. Git merge of `astra/unit-anim-3d-v2` (9c35ac22)
failed on ORIG_HEAD.lock. Applied its exact binary/text file delta to the clean
lane worktree instead. Staging also failed on index.lock. No push or PR.
Runner handoff: `lanes/spearman-r15b/round15b-only.patch` contains only these
seven lane files relative to R14; `commit-message.txt` includes the requested
co-author. No changes to docs/learnings or unrelated art/design/rules.

## Selected work

The apparent pale sole includes the rolled instep skin and straps. Object-ID
render and evaluated ray hits establish that; simply darkening downward-facing
sole polygons misses the exposed patch. Frozen per-foot masks shade existing
pigment smoothly with evaluated foot tilt in MOVE ONLY. Rest and the other four
clips keep their foot pigment. No mesh, weights, UVs, camera, donor foot rotation,
keyframes, timing, frame count, cloth or saved master was edited.

Move uses two compact, soft 40%-strength pools, anchored to evaluated articulated
sole centroids before every render. They fade with mean sole clearance. Contact
reach is 25 mm, contact depth .2, cast depth .08. Anchors match evaluated centers
exactly at all eight delivered samples; measured forward/backward spans are
0.798 m left and 0.750 m right, so these are not static stone marks.

The rest-shadow change is NOT selected. The cloud reviewer says to keep R14 on
metric regression. The 09:48Z art director endorsed the sole-fix direction but
rejected the gentler continuous band, requesting two 12 px pools at 40% strength.
That exact alternative is implemented with `ground_pools=1`, rendered separately
and included in the host A/B. It removes the stripe but materially worsens the
feet metric. The selected default therefore retains R14's rest/held-clip shadow;
the lead must resolve this visual-versus-metric tradeoff after the GPU comparison.

## Matched evidence (Cycles CPU proxy, 256 px, 8 samples, seed 17)

Same preserved R14 master/clip and calibration for both variants; source/code
hashes and effective per-clip settings are in
`lanes/spearman-r15b/selected/proxy/receipt.json`. Do not compare these improvement
numbers with R14's GPU metrics or its older CPU calibration.

| Measurement | R14 settings | Selected R15b | Rest pools alternative |
| --- | ---: | ---: | ---: |
| Rest IoU, zero/best offset | .951254 | .951254 | .951254 |
| Rest blurred delta-E | 3.330594 | 3.330594 | 3.981121 |
| Feet blurred delta-E | 5.447247 | 5.447247 | 10.941275 |
| Base blurred delta-E | 3.232251 | 3.232251 | 3.239231 |

Selected rest RGBA is byte-identical to the matched R14 render. An earlier wider
soft band measured 3.2961 overall / 5.1769 feet, but was rejected visually; those
numbers are not the final selection. The initial compact 50% rest profile was
also rejected (feet 10.883).

Move sample 1 foot-box mean luminance 85.5 -> 58.2. Using the same fixed BEFORE
foot mask on both sides (alpha >240, display luma <145, to exclude the cream base
and greave in each box), sample 1 mean/p90 is 80.22/101.31 -> 51.01/64.59, and
sample 5 is 74.47/104.38 -> 52.12/74.53. Boxes and both full-box and masked numbers
are recorded in `spearman-r15b-cpu-metrics.json`; no claim that an entire box is
pure sole. The painting is shown at native 256/160 and its own 64 px token.

Review files under `review/3d-v2/`:
- `spearman-r15b-cpu-rest-{256,160,64}.png`: selected rest is unchanged.
- `spearman-r15b-cpu-move-{256,160,64}.png`: fresh matched full walk + painting.
- `spearman-r15b-cpu-pools-rest-{256,160,64}.png`: unselected requested pools.
- `spearman-r15b-sole-id.png`, `-identify-crop.png`: material identification.
- `spearman-r15b-g-feet-check.png`: fresh 33-sample top/front GEOMETRY diagnostic
  with saved materials, not the final look; use the move strip for pigment.
- `spearman-r15b-critique-*`: selected rest critique and all 40 fresh CPU frames.
- `spearman-r15b-shadow-options.png`: rejected rest explorations, not delivery.

## Checks and verdict

- 36 tests pass: kit 27, look 3, pipeline 2, critique 4; look's 3 repeated after
  final edits. Zero unresolved imports, 116 Python files parse, diff whitespace
  clean, gpu.sh syntax/executable checks pass.
- Fresh 40-pose audit: zero findings. Dense 33-sample foot check: no failures;
  planted slip .004234 mm, floor error .000106 mm, heading 5.142 degrees,
  readable heading 9.175 degrees, loop seam zero. Contact limits were not relaxed.
- A/B asserts original geometry, weights, UVs and action hashes unchanged on
  material application; evaluated rig pose unchanged per rendered frame.
- All five clips freshly rendered (8/8/10/4/10), inspected in the contact sheet.
  Rest critique ran on the final selected render. No new atlas was shipped.
- The first feet check failed because the isolated review directory was absent;
  created it and reran successfully. This was an output-path issue, not contact.

At 256 the walk's light dot is suppressed and painted foot detail remains;
registered rest remains close but simpler than the painting. At 160 the moving
feet no longer flick to a pale patch. At 64 it is the same readable unit, with
no claimed rest improvement. The rest shadow stripe remains the unresolved
part of this lane. No PASS marker and no GPU verification claim.

Host command from repo root: `ROUND=15 tools/art/anim3d/units/spearman/gpu.sh`.
It retains all stages, 512/256 masters, trimmed 160 atlas/validation, top/front
feet and eight-second five-clip movie. Its added A/B calls the SAME
`look.configure_render` and `look.render_frame` functions for R14 foot settings,
selected R15b and the opt-in rest pools. It writes `spearman-r15b-gpu-*`, including
native-size comparisons and metrics. Metal is unavailable in this sandbox;
those GPU images are prepared to run, not represented as existing evidence.

## Learnings for the lead's skill merge

1. A reviewer naming a "sole" does not identify the material: this flash is
   mostly instep/straps. Render IDs before changing masks or sole textures.
2. An ankle marker can move correctly while a broad overlapping shadow still
   looks stationary. Measure evaluated centers AND inspect the visible footprint.
3. Smaller/lighter shadows can look cleaner yet double a regional colour error.
   Conversely, a better average can retain a visibly bad stripe. Preserve both
   evidence streams; don't use either as an automatic art PASS.
4. Compare shader variants on one preserved master through the delivery frame
   function. Refresh shader markers after frame_set, and include new shader
   modules in calibration hashes. Keep the approved rest independent of a
   motion-only pigment correction.
