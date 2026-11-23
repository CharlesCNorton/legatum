# Rocket artillery — round 1 candidate

Original full-depth six-wheel truck and forty-tube launcher, mechanically rigged in
Blender. The painting is frozen onto finished 3D surfaces; unseen faces use the
recorded generated olive fill. Tire projection uses an isolated wheel region so
body fragments cannot rotate with wheels. Three real AO/curvature bake pairs,
beveled bodywork and fittings, product lights, cream stone, and one measured grade
are included. Scripts and the v2 candidate atlas live in git; editable masters,
bakes, frames and review evidence live under `~/LegatumRuns/anim-pilot/`.

From the repo root:

```sh
RESOLUTION=256 SAMPLES=8 tools/art/anim3d/units/rocket-artillery/render.sh stills
RESOLUTION=512 SAMPLES=4 tools/art/anim3d/units/rocket-artillery/render.sh preview
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/rocket-artillery/check.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/rocket-artillery/deliver.py
```

Complete lead-side GPU run (no arguments):

```sh
ROUND=1 tools/art/anim3d/units/rocket-artillery/gpu.sh
```

The script first checks Metal without changing prior evidence. Then it rebuilds,
bakes and renders all stages at GPU512/64 samples; creates 256 masters; packs and
validates the trimmed 160px atlas; makes the eight-second five-clip MP4; and writes
a receipt only after independent GPU/source/hash checks. Blender always runs via
the PATH gate. The GPU log/status file identifies any failed stage. CPU frames
remain explicitly labeled CPU, even when they are genuine 512px renders.

Review files are `review/3d-v2/rocket-artillery-{b-plain,c-textured-lit,c-details,
d-rig-poses,e-<clip>-strip,f-restpose-compare,g-feet-check}.png`, five animated
`e-<clip>.webp` files, and `rocket-artillery-round${ROUND}.mp4`. The plain sheet
includes actual side and rear views. The feet sheet is an eight-sample top/front
wheel inspection: no person/animal exists in this unit. The external log records
observations; `round1-first/` preserves early CPU evidence.

The five clips have 8/8/10/4/10 frames. All six wheel controls use the same nominal
rolling radius, common travel/radius rotation and an exact one-revolution loop;
all wheel bottoms are checked against the stone at every sample. The static token
uses treadmill motion; the runtime would supply translation. Death lowers the
launcher and suspension into a held disabled pose. Effects use keyed visibility
with positive real geometry, never zero scale. Camera, base and world lighting
remain fixed for the clip renders.

Atlas JSON has `version:2`, `trimmed:true`, logical frame 160x160, anchor
`(80,121.25)` and ordered `clips` with `row/frames/fps/loop/rects`. A rect contains
`x/y/w/h` in the atlas and `ox/oy` in the logical cell. Draw at
`(anchorX-ax+ox,anchorY-ay+oy)`. No renderer integration is part of this candidate.
The packer preserves all frames and quality >=75; exceeding 200,000 bytes fails.
It checks exact decoded alpha reconstruction, motion and identical death holds.
The manifest also binds the model, clip blends, scripts, source/fill, grade, raw
frames and 256 gallery. Video validation checks H.264/yuv420p, 240 frames, eight
seconds and 1600x348 dimensions.

Art verdict: **not a PASS**. At 64px it reads as the same raised rocket truck. At
256px the painted finish is much closer than plain procedural paint, but tube rim
registration, over-bright far wheels, tire proportions, cab/fender fit, stone brushwork and oblique
mechanical construction still need refinement. Projected lighting moves with the
wheels and launcher; wider motion reveals less convincing hidden surfaces. The
GPU pass and the lead's visual review are outstanding. No PASS marker is written
by automation, and the existing painting remains the runtime asset.

Non-obvious rig finding: moving a wheel through `matrix_world` can decompose a
continuous turn into wrapped Euler angles. Contact correction now changes only
parent-space location; the validator checks travel/radius at all nine move keys,
including the closing key. This preserves continuous editable rolling curves.

Round-one verification: CPU Cycles, actual 512px renders at four preview samples,
40 graded 256px frames; atlas 1368x595, **193,574 bytes at quality 78**. The
source/model/clip/grade/gallery hashes, six-wheel travel and contact, whole-vehicle
ground clearance, all forty reconstructed alpha masks and exact death hold pass.
The decoded-atlas movie passes FFprobe: H.264/yuv420p, 1600x348, 240 frames, 8.0s.
A decoded video frame was visually inspected. Python compilation, shell syntax and
`git diff --check` pass. The complete GPU entry point was exercised and stopped
at Metal preflight as expected in this sandbox, preserving CPU evidence. GPU
renders and visual approval remain pending. Git could not create the worktree's
`index.lock`; changes are left uncommitted for the runner. No Rust/UI runtime code
changed, and no full engine/browser test suite was run for this asset-only lane.
