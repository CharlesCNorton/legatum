# Howitzer animation, round 1

True 3D candidate matching the original uncrewed gun: hollow short elevated tube,
recuperators, thick shield, dished twelve-spoke steel wheels, stepped hubs,
carriage cheeks, elevation handwheel, bolted trails and one fixed cream disc.
Mechanical parent controls form the editable rig. No painting plane, relief card,
image clipping or runtime change. This is an art candidate, not approved replacement art.

From the repository root:

```sh
RESOLUTION=256 SAMPLES=8 tools/art/anim3d/units/howitzer/render.sh stills
RESOLUTION=512 SAMPLES=8 tools/art/anim3d/units/howitzer/render.sh preview
source tools/art/anim3d/env.sh
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/howitzer/audit.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/howitzer/check.py
~/LegatumRuns/anim-pilot/venv/bin/python tools/art/anim3d/units/howitzer/deliver.py
```

CPU renders are previews even at 512px. The lead's complete no-argument host pass is:

```sh
ROUND=1 tools/art/anim3d/units/howitzer/gpu.sh
```

It rebuilds and bakes the scene, renders every stage and all 40 clip frames with
Metal Cycles at 512px/64 samples (no silent CPU fallback), keeps 512 masters and
graded 256 derivatives, checks provenance and wheel contact, packs/validates the
160px trimmed atlas, and writes the eight-second H.264/yuv420p five-clip review.
The driver sets ROUND. Stage status, transcript and a GPU success receipt are
external. A technical receipt never writes a PASS marker.

External outputs under `~/LegatumRuns/anim-pilot/`:

- `assets/howitzer/`: original painting, registered texture and generated fill.
- `masters/howitzer/`: plain/final/five clip .blend files, actual AO and curvature
  maps, raw renders, 512 and 256 sets, grade, geometry/contact/provenance reports.
- `review/3d-v2/howitzer-*`: immediate plain multi-view, textured, detail, rig pose,
  five PNG strips and animated WebPs, painting/rest/crossfade at 256/64, top/front
  move contact sheet and `howitzer-round${ROUND}.mp4`.

Shipped candidate: `app/src/assets/units/anim/howitzer.{webp,json}`. The atlas has
40 logical 160-square frames, five trimmed rows, quality >=75 and <=200,000 bytes.
Each clip's `rects` list contains atlas `(x,y,w,h)` and logical `(ox,oy)` offsets.
Draw at `(X + (ox-ax)*s, Y + (oy-ay)*s)` for display scale s and anchor (X,Y).
Do not treat `row` as a fixed grid coordinate. Runtime support remains outside this lane.

Review limitations: camera matching is approximate; the rest view remains visibly
different from the painting. Spokes deliberately retain real worn-metal material
to avoid doubled lines from projected spokes. Hidden sides use generated fill;
the base has live contact shading rather than frozen source wheel shadows.
Fresh host GPU output needs visual review. Do not infer art approval from validation.

Round-one verified delivery: **188,042 bytes at Q80**, 1329x700 atlas, all 40 frames.
Delivery alpha uses 32 levels, as in the shared pipeline; 512/256 masters keep full
alpha. Every decoded quantized mask reconstructs exactly. The saved-clip audit
passes all 40 wheel contacts, loop closure, stationary base, nondegenerate meshes,
held death and six baked maps. MP4: 240 frames, eight seconds, H.264/yuv420p,
1600x348. Python/shell syntax and stale-grade/model/CPU-as-GPU rejection checks pass.
Postprocessing scripts are versioned separately from the render inputs; changing
the packer does not claim that the unchanged Blender frames were re-rendered.

Art verdict: not PASS. At 256px the wheels are too clean/flat, the lower carriage
and trail differ, and the cream base lacks the painting's subtle surface richness.
At 64px the howitzer identity is clear, but it is distinguishable from the painting.
Rest silhouette IoU .827851 and opaque-overlap RGB MAE 30.0975 are diagnostic only.
GPU64 rendering has not run in the sandbox. Current masters are real CPU512/8,
not final GPU evidence. Git index.lock is denied; runner must commit using the
message saved in external masters/howitzer/commit-message.txt.
