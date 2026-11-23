# War Elephant — round 1 candidate

This is an art candidate, not an approved replacement for the painting. No runtime
loader or game rule changes. The elephant, articulated trunk, ears, tusks, harness,
cloth, timber howdah and equipment are original volumetric Blender geometry.
Two independently created MPFB males supply the officer and mahout anatomy and
skin weights. The elephant has a 20-bone authored skeleton. There is no downloaded
elephant model, billboard, relief cutout or commercial service.

The original painting is frozen-camera UV colour on the actual posed meshes, with
an incidence/alpha blend into generated grey skin, red textile, wood and linen
fills. Texture alpha controls colour blending only; it never cuts the model's
silhouette. Unseen surfaces retain depth and materials. The texture does contain
painted lighting, so rest registration and motion seams need visual review.
Noise bump, thick cloth, raised quilt stitching, bevelled individual howdah planks,
posts, bronze rivets, rope harness, curled tusks and toenails add physical detail.
Lighting is a warm upper-left area key, cool rim and soft fill. A single restrained
histogram transfer, fitted from the rest render, grades every clip consistently.
The base is stationary warm cream stone, with pigment aimed at sRGB #E9CFA0.

## Inputs and reproduction

All masters and generated fills stay outside git in
`~/LegatumRuns/anim-pilot/{assets,masters}/war-elephant/`. `assets.lock.json` pins
both art inputs; `fills.prompt.txt` records the built-in imagegen prompt and output.
The existing MPFB 2.0.18 installation and its CC0 system assets are required; use
the parent playbook's setup. Do not silently regenerate a missing fill master.

```sh
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/war-elephant
"$ANIM_ROOT/venv/bin/python" "$unit/prepare.py"
"$unit/run.sh" build
RESOLUTION=256 "$unit/run.sh" b
"$unit/run.sh" c
"$unit/run.sh" animate
"$unit/run.sh" audit
RESOLUTION=256 "$unit/run.sh" d
# Run stages separately; one Blender process from this lane at a time.
"$unit/run.sh" e-idle
"$unit/run.sh" e-move
"$unit/run.sh" e-attack
"$unit/run.sh" e-hit
"$unit/run.sh" e-death
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" pack
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" validate
ROUND=1 "$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" video
```

Every invocation is background Blender, disables autoexec, and goes through the
shared `bin/blender-slot` gate. CPU previews default to Cycles, four samples and
512 px. No new dependency installs. Final host GPU rerender:

```sh
ROUND=1 tools/art/anim3d/units/war-elephant/gpu.sh
```

That renders all clips at 512 px with Cycles Metal, 32 samples and denoising;
`SAMPLES=64` raises quality. It refuses a silent CPU fallback. An explicit
`RENDER_ENGINE=BLENDER_EEVEE` uses the Metal Eevee backend. It refreshes the rest
LUT before every clip, then packs, validates and writes the review MP4. Geometry
changes require build and animate first. All raw 512 frames and graded 256 gallery
frames remain in the unit's master directory. A failed render invalidates its
manifest. Packing verifies master/clip/render/grade hashes to reject stale output.

## Motion and delivery

The clips are idle 8, move 8, attack 10, hit 4, death 10 at 10/12/14/12/10 fps.
Idle has breathing, ear, trunk and tail motion; move is an authored four-beat
walking cycle. Attack braces and drives the head/tusks forward while the officer leans through his spine rig, then recovers.
Hit recoils through the head and trunk. Death folds the legs, rolls onto a side and holds its last two frames.
The howdah and riders follow the body. No motion capture or cloth physics is
claimed. Ground correction across all clips is authored geometry contact, not rigid-body
simulation. Inspect the gait, attachments and collapsed rider/howdah intersections.

The v2 atlas keeps a logical 160×160 canvas and anchor `(79,138)`. All 40 frames
are individually alpha-trimmed with two pixels of atlas padding on each side:

```json
{"version":2,"layout":"trimmed","frame":{"w":160,"h":160,"ax":79,"ay":138},
 "clips":{"idle":{"row":0,"frames":8,"fps":10,"loop":true,
 "rects":[{"x":2,"y":2,"w":120,"h":145,"ox":20,"oy":8}]}}}
```

The example rectangle is illustrative. `rects` has one entry per actual frame:
crop the atlas at `x,y,w,h`, paste at `ox,oy` in a transparent logical canvas, then
apply the anchor. `row` is descriptive only: **legacy fixed-cell row sampling is
incorrect for this atlas**. The painting remains the runtime asset until a shared
trim-aware loader and art approval land. Packing tests qualities 90, 85, 80, 75;
it refuses over 200,000 bytes at 75 and never drops frames. The review video
reconstructs the trimmed frames, scales them 2×, and loops all five side by side
on cream for eight seconds, H.264/yuv420p, 30 fps.

`audit.py` checks anatomy, weights, projection, base/camera stability, body contact,
loop closure and held death. `deliver.py validate` checks frame counts, alpha,
bounds, motion, trim rectangles, hashes and the byte/quality caps. These are
technical checks, not art approval or a full collision solver.

The six Blender skills informed the work: modeling (continuous remeshed anatomy,
thickness and bevels); materials (painted fills, bump and physical materials);
animation (anticipation, recovery, cyclic keys and held death); cameras (fixed
orthographic painting view); lighting (three area lights); rendering (small CPU
previews, retained PNG sequences, explicit GPU mode and encoded review video).

## Round-one visual verdict

The 64 px token reads as the same elephant/howdah unit, but the 256 px comparison
is readily distinguishable from the painting. The blanket is too broad and
rectangular, the ears lack the painting's shape, the riders' poses need closer
registration, and the base remains too dull. The death views reveal shoulder-cloth
projection spill and rigid riders, and the folded legs leave the body supported
too high. These are visible art/animation defects, not a GPU sampling issue.
No `war-elephant-PASS` marker is written. Preserve the painting in the game and
use the split/crossfade and death strip to direct the next modeling round.
