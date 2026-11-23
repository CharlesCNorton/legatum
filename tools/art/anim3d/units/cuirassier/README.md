# Cuirassier round 1

True Blender geometry: a CC0 Quaternius skinned horse, a CC0 MPFB anatomical rider,
original steel armour with rolled gilt edges, perforated visor, thick tack,
stirrups and a wheellock pistol. The horse retains its source skeletal actions;
the rider has authored aim, recoil, breathing, hit and death keys. Smoke is actual
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
The full original painting is registered to the token, projected to frozen UVs
on the actual deformed rest mesh, then carried by the skin weights through motion.
Incidence/alpha and pigment masks blend into generated painted fills on hidden
surfaces. The reused fill sources and their original generation are recorded in
`assets/SOURCES.md`. One rest-derived histogram grade applies to every clip.

## Lead GPU pass

```sh
ROUND=1 tools/art/anim3d/units/cuirassier/gpu.sh
```

This uses Cycles Metal GPU, refuses CPU fallback, renders all review stages and
40 clip samples at 512 px, retains 512 and 256 masters, writes the trimmed 160 px
atlas and JSON, validates them, and writes `cuirassier-round${ROUND}.mp4` (eight
seconds, all five clips side by side at 2x, H.264 yuv420p on cream). It also emits
the rest comparison, detail crops and animated WebP reviews. GPU quality still
needs visual review; no PASS marker is generated automatically.

## Atlas contract

`frame` describes the **untrimmed virtual 160 x 160 cell** and anchor `(103,140)`.
`clips` retain logical rows idle/move/attack/hit/death and frame counts 8/8/10/4/10.
Each clip adds `rects`, one `{x,y,w,h,ox,oy}` per frame: source rectangle in the
packed atlas and the top-left offset in its virtual cell. Restore a cell by
pasting that rectangle at `(ox,oy)`; draw relative to `(ax,ay)` after restoration.
Physical row heights and widths vary. There are two transparent gutter pixels
around every tile. WebP is quality 75 or above, at most 200,000 bytes.

This is a candidate asset. The app's static painting remains in use; no runtime
loader was changed. A legacy fixed-grid reader cannot interpret this format.
