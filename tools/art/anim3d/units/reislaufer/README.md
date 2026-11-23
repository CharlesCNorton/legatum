# Reislaufer — round 1 candidate

Run from the repository root. Every Blender call uses the `blender` PATH gate,
background mode and disabled automatic script execution. Stages are serial.

```sh
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/reislaufer/prepare.py
SAMPLES=12 RESOLUTION=256 tools/art/anim3d/units/reislaufer/render.sh build
tools/art/anim3d/units/reislaufer/render.sh animate
SAMPLES=12 RESOLUTION=256 tools/art/anim3d/units/reislaufer/render.sh preview
tools/art/anim3d/units/reislaufer/render.sh audit
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/reislaufer/finish.py pack
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/reislaufer/test_delivery.py
```

`build` posts plain clay immediately, then bakes AO/curvature and posts the
painting-projected rest, details and 50/50 comparison. `preview` posts four rig
poses, each complete clip strip/animated WebP immediately, and both foot views.
All masters are external in `masters/reislaufer/`; reviews and the running log
are in `review/3d-v2/reislaufer-*`. All inputs are external in `assets/reislaufer/`.

The complete, no-argument GPU entry point is:

```sh
ROUND=1 tools/art/anim3d/units/reislaufer/gpu.sh
```

It requires Metal Cycles, refuses CPU fallback, rebuilds the model/materials and
all five actions, renders every stage at 512, retains 512 and 256 sets, makes the
trimmed 160 atlas, verifies hashes/alpha/40 frames/terminal hold, runs delivery
regressions, and writes the decoded-atlas eight-second H.264 movie. The driver
sets ROUND. A technical GPU receipt never writes PASS; actual art review is still
required. CPU previews are labelled in the render/pack manifests and cannot issue
a GPU receipt. The painting remains the runtime art.

Atlas v2 is `{version,unit,frame:{w,h,ax,ay},atlas:{w,h},clips}`. Each clip contains
`row,frames,fps,loop,rects:[{x,y,w,h,ox,oy}]`. Reconstruct at `(ox,oy)` in a 160 cell,
or draw at `anchor + (ox-ax,oy-ay)*scale`. The anchor is `(80,145)`. Never infer
rectangles from fixed row cells. Frame counts are 8/8/10/4/10, quality >=75,
file size <=200000 bytes. The movie uses the decoded cropped atlas, not masters.

See `REVIEW.md` for the honest visual verdict and remaining defects.
