# Cuirassier GPU follow-up, driver round 2

True Blender geometry: a CC0 Quaternius skinned horse, a CC0 MPFB anatomical rider,
original steel armour with rolled gilt edges, perforated visor, thick tack,
stirrups and a wheellock pistol. The horse retains its source skeletal actions;
the rider uses CC0 Quaternius seated/hit/death torso and head deltas with
reference-pose and bone-roll compensation. Pistol aim/recoil is authored; legs
and reins stay constrained to the saddle. Smoke is actual
opaque mesh volume with keyed render visibility. There are no billboards.

## Rebuild and CPU review

From the repository root, after the common MPFB installation and mounted horse
asset are present:

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/cuirassier/prepare.py
tools/art/anim3d/units/cuirassier/render.sh build
tools/art/anim3d/units/cuirassier/render.sh paint
tools/art/anim3d/units/cuirassier/render.sh animate
tools/art/anim3d/units/cuirassier/render.sh audit
RENDER_ENGINE=CYCLES CYCLES_DEVICE=CPU SAMPLES=4 RESOLUTION=256 tools/art/anim3d/units/cuirassier/render.sh render
CYCLES_DEVICE=CPU RESOLUTION=192 SAMPLES=4 tools/art/anim3d/units/cuirassier/render.sh feet
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/cuirassier/feet_sheet.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/cuirassier/pack.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/cuirassier/validate.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/cuirassier/video.py
```

Every Blender invocation uses plain `blender` on PATH, in background mode, with
Python exceptions propagated as failure. One process performs each stage serially.
`STAGES=c,c-details` restricts rendering for an iteration. All `.blend`, input
images, bakes, raw renders, grade LUTs and 512/256 masters live outside git in
`~/LegatumRuns/anim-pilot/{assets,masters}/cuirassier/`.

`paint.py` bakes real 256 px AO and Pointiness maps for breastplate and visor.
It calls `refine.py` to finish rigid surfaces, freeze MPFB macro keys and fit
full-depth anatomy through inverse skin matrices before freezing the UVs.
The full original painting is registered to the token, projected to frozen UVs
on the actual deformed rest mesh, then carried by the skin weights through motion.
Ray visibility, incidence and source alpha blend into generated painted fills on hidden
surfaces. The reused fill sources and their original generation are recorded in
`assets/SOURCES.md`. One rest-derived histogram grade applies to every clip.

## Lead GPU pass

```sh
ROUND=2 tools/art/anim3d/units/cuirassier/gpu.sh
```

This first verifies Metal and rebuilds paint, clips and the geometry audit.
It uses Cycles Metal GPU, refuses CPU fallback, renders all review stages and
40 clip samples at 512 px, retains 512 and 256 masters, writes the trimmed 160 px
atlas and JSON, validates them, and writes `cuirassier-round${ROUND}.mp4` (eight
seconds, all five clips side by side at 2x, H.264 yuv420p on cream). It also emits
the rest comparison, detail crops, animated WebP reviews and a full eight-sample
top/front hoof sheet (`cuirassier-g-feet-check.png`). GPU quality still
needs visual review; no PASS marker is generated automatically.
The script retains `gpu-logs-cuirassier-r${ROUND}.log`, updates
`review/3d-v2/cuirassier-gpu-status.txt`, and writes a round receipt only after
checking current GPU512/gallery256 output and probing the encoded MP4.

## Atlas contract

`frame` describes the **untrimmed virtual 160 x 160 cell** and anchor `(103,140)`.
`clips` retain logical rows idle/move/attack/hit/death and frame counts 8/8/10/4/10.
Each clip adds `rects`, one `{x,y,w,h,ox,oy}` per frame: source rectangle in the
packed atlas and the top-left offset in its virtual cell. Restore a cell by
pasting that rectangle at `(ox,oy)`; draw relative to `(ax,ay)` after restoration.
Physical row heights and widths vary. There are two transparent gutter pixels
around every tile. WebP is quality 75 or above, at most 200,000 bytes.
Reduction is premultiplied bicubic with unquantized alpha. Identical samples may
share a rectangle. Source and decoded death holds must both be pixel-identical.

This is a candidate asset. The app's static painting remains in use; no runtime
loader was changed. A legacy fixed-grid reader cannot interpret this format.

The preceding GPU round passed technical delivery (199,170 bytes, Q85,
Cycles GPU64 at 512 px), but visibly missed the painting and had a floating
terminal collapse. That evidence is archived under `masters/cuirassier/driver-r1-gpu`.
Current CPU/GPU measurements and candid visual verdicts are in the external
`review/3d-v2/cuirassier-log.md`. Successful validation is not painting parity.
No art PASS is produced by any script.

The revised projection preserves warm bridle paint instead of rejecting it by
hue. Only cream stone pixels project onto the base, so standing hooves cannot
appear after the mount moves. Source pigment is frozen in mesh UVs, with actual
full-depth residual fitting of head, hind legs, withers and axilla. This remains
an approximate anatomical registration to a single painting, not proof of exact
camera recovery. Native horse foot rotations are retained.

Driver round-2 CPU delivery: all 40 samples at Cycles CPU8 / 256 px, trimmed
160 px atlas 185,984 bytes at Q80 (1281 x 751). Geometry/alpha/bounds/hash/motion/
held-death checks pass; terminal torso separation is 0.114 m. The eight-second
H.264/yuv420p movie has 192 frames; four delivery regressions pass. This is still
below the art bar: head/leg shape, foot support, motion texture reveals and the
rider terminal pose need further work. Fresh GPU512 rendering remains pending.
