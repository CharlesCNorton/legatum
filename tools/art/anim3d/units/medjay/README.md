# Medjay, round 2

True 3D MPFB anatomy and 53-bone skeleton, original folded linen kilt, solid
headband, curved feather, convex hide shield and bronze spear. The original
19,158-vertex body cage stays in the plain master; finished geometry freezes
subdivision before projection and retains interpolated native skin weights.
Eight actual AO/curvature bake pairs and generated hidden-surface fills remain
outside git. No billboard or per-frame texture reprojection is used.

Run from the repository root:

```sh
tools/art/anim3d/units/medjay/render.sh build
tools/art/anim3d/units/medjay/render.sh finish
tools/art/anim3d/units/medjay/render.sh animate
ROUND=2 tools/art/anim3d/units/medjay/gpu.sh
```

The executable no-argument GPU handoff requires Cycles Metal, renders every stage
at 512 px / at least 64 samples, retains matching 256 px copies, creates the
rest comparison, strips and animated WebPs, audits the geometry, packs and
validates the trimmed atlas, then writes the eight-second five-clip H.264/yuv420p
`medjay-round${ROUND}.mp4`. It records a round log, failure status and successful
technical receipt; it never writes an art PASS. CPU preview: use
`RESOLUTION=256 SAMPLES=8 render.sh <stage>` with the full path above.

External root: `~/LegatumRuns/anim-pilot`. Sources: `assets/medjay`; editable
masters, raw/graded frames, bakes and checks: `masters/medjay`; reviews:
`review/3d-v2/medjay-*`. The prior round is preserved in `masters/medjay/round1-cpu`.
Source painting and generated fills are unchanged and pinned in `assets.lock.json`.

`app/src/assets/units/anim/medjay.{webp,json}` remains an unwired art candidate.
Version 2 uses logical `frame:{w:160,h:160,ax:84,ay:141}` and ordered clip `rects`
with `{x,y,w,h,ox,oy}`. Reconstruct crops at their offsets before applying the
anchor; physical atlas rows have variable heights. Full alpha is retained,
identical frames share rectangles, and all 8/8/10/4/10 samples remain. Quality
never falls below 75; over 200,000 bytes fails without replacing the atlas.

Round-two changes: upright head and fitted cranial vault, narrow feather, solid
headband, fitted calves/toes, closed linen waist gap, thinner cream base,
finished-surface UVs and camera-only painted illumination. Generated fills,
physical shading and product lights remain on revealed surfaces. Combat entries
match the rest pose; planted move targets compensate root bob.

The painting remains visibly richer at 256 px. At 64 px Medjay is recognizable,
but the anatomy, gaze, base finish and silhouette still differ. No PASS marker.
Full collision freedom and final GPU art quality are not established by the
structural/UV audit. Exact round results are in `medjay-log.md` and the pack,
validation and audit JSON reports under the external master directory.

Round-two CPU verification: all 40 frames retained at 512 and 256 px, Cycles
CPU8; trimmed 160 px WebP **157,968 bytes at quality 90**, full lossless alpha.
Atlas reconstruction, identical decoded death hold, current render/grade/master
hashes, rig/finished-UV/combat-entry audit, Python/Bash syntax and whitespace
checks pass. MP4 verified H.264/yuv420p, 1600 x 348, 30 fps, 240 frames, 8 seconds.
Silhouette alpha IoU improves from .776736 to .802003. The painting remains
visibly different; **no art PASS and no verified GPU render**.
