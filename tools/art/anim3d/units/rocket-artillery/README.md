# Rocket artillery — round 2 candidate

Original full-depth six-wheel truck and forty-tube launcher, mechanically rigged
in Blender. The painting supplies frozen camera UVs on finished surfaces; unseen
faces use the recorded image-generated olive fill. Three actual AO/curvature bake
pairs, beveled panels, solid straps/fittings, hollow bores, tire tread and product
lighting are retained. Masters and review evidence remain outside git under
`~/LegatumRuns/anim-pilot/`.

Round 1's GPU pass succeeded (189,894 bytes at quality 75), but the bright wheel
copies, exposed far wheels and broad stone silhouette failed the visual bar.
Round 2 lowers the camera, registers the disc and far wheels again, separates
near-wheel and far-wheel pigment, softens tread blocks and makes the rocket
flight visible. Clean top/rim swatches from the painting wrap the actual stone;
no wheel silhouettes or static contact shadows are copied onto it. The existing
generated olive fill remains on unseen vehicle surfaces. RGB histogram quantiles
are matched at native 256px, bounded to twelve channel values, and frozen across
all clips. Alpha is unchanged.

From the repository root:

```sh
RESOLUTION=256 SAMPLES=8 tools/art/anim3d/units/rocket-artillery/render.sh stills
RESOLUTION=512 SAMPLES=8 tools/art/anim3d/units/rocket-artillery/render.sh preview
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/rocket-artillery/check.py
ROUND=2 "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/rocket-artillery/deliver.py
```

Complete no-argument lead-side GPU pass:

```sh
ROUND=2 tools/art/anim3d/units/rocket-artillery/gpu.sh
```

The script checks Metal before changing evidence, then rebuilds, bakes and renders
all stages at GPU512/64 samples. It creates 256px masters, packs and validates the
trimmed 160px atlas, writes the eight-second five-clip MP4, and issues a receipt
only after independent GPU/source/hash checks. It tees output to the driver and
`rocket-artillery-gpu-pass-r${ROUND}.log`. Missing Metal fails explicitly. Every
Blender call uses the plain PATH gate; CPU evidence is never labeled GPU.

Review images are published immediately as `rocket-artillery-{b-plain,
c-textured-lit,c-details,d-rig-poses,e-<clip>-strip,f-restpose-compare,
g-feet-check}.png`, with five animated `e-<clip>.webp` files. The rest comparison
shows painting/render/crossfade at native 256 and 64px. The plain sheet includes
side/rear geometry; the top/front wheel sheet spans all eight move samples.
Round 1's GPU images and movie are preserved in
`review/3d-v2/rocket-artillery-round1-preserved/`.

Clips retain 8/8/10/4/10 frames for idle/move/attack/hit/death. All six wheels use
common travel/radius rotation and a closing one-revolution key. Contact correction
changes only parent-space translation, preserving continuous Euler rotation.
The audit checks ground height, contact points inside the disc, stationary stone,
positive mesh scales and whole-vehicle clearance at every sampled pose. Death
holds its final two frames exactly. Effects use keyed visibility and solid meshes.
There is no person or animal, so motion capture and feet retargeting do not apply.

Atlas metadata is v2 `trimmed-rows`: logical 160px cells, anchor `(80,121.25)`,
ordered idle/move/attack/hit/death clips, and per-frame rectangles with atlas
`x/y/w/h` plus logical `ox/oy`. Draw at `(X-ax+ox,Y-ay+oy)`. All forty frames remain,
WebP quality must be at least 75, and bytes must not exceed 200,000. Validation
reconstructs every decoded alpha mask and checks the held death. The manifest
binds source/fill, model, scripts, clip blends, grade, raw renders and 256px gallery.
The movie reconstructs decoded trimmed frames, shows all five clips at 2x on
cream, and verifies H.264/yuv420p, 1600x348, 240 frames and eight seconds.

**Art verdict: not a PASS.** The three-axle silhouette is closer at 64px. At 256px,
cab and launcher paint carry the reference detail, but tire volume/tread, launcher
mouth registration and stone shading still reveal the reconstruction. Painted
wheel illumination rotates with the tires; oblique construction and hidden
surfaces remain weaker than the fixed view. Round 2 needs fresh GPU review. The
pipeline never writes the PASS marker, and no app runtime wiring is changed.

Round-two CPU verification: Blender Cycles, actual 512px renders at eight samples,
40 graded 256px frames; atlas **1368x603, 186,860 bytes at quality 75**. Pipeline,
model, clip, grade and gallery hashes pass; all wheel travel/radius keys and ground
contacts pass, with maximum contact radius 1.634 inside the 1.76 disc. All forty
trimmed alpha masks reconstruct exactly; final death frames are identical.
FFprobe confirms H.264/yuv420p, 1600x348, 240 frames, eight seconds. Decoded movie
frames at 0.3/0.6/1.4 seconds were inspected. Python compilation, shell syntax,
executable handoff and whitespace checks pass. No Rust or UI code changed.
