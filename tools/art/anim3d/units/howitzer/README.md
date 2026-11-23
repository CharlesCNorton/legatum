# Howitzer animation, round 2

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
ROUND=2 tools/art/anim3d/units/howitzer/gpu.sh
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

Round-two changes: deeper rolled rims, 96 solid rim rivets, beveled spokes and
sockets fitted to source landmarks and constrained inside physical wheel radii,
continuous source-metal swatch wheel pigment, generated paint on unseen faces, masked source stone pigment and
camera-visible grain. Projection occluders now exclude hidden geometry. Original
input hashes are checked before every build. GPU logs also reach the driver.

The supplied round-one GPU pass succeeded: **187,034 bytes at Q75**, actual
512px/64-sample Metal masters, all forty frames and eight-second H.264 movie.
That evidence is preserved in external `masters/howitzer/driver-r1-gpu/`.
Round-two CPU preview and validation results are recorded in the running
`review/3d-v2/howitzer-log.md`; CPU output is never GPU evidence.

Art verdict: not PASS. The wider finished rims and cream stone are closer, and
64px identity remains clear. Hub/spoke registration, the lower carriage and trail,
and some bright/dark boundaries still differ at 256px. There is no painting-parity
claim and no PASS marker. Camera matching remains approximate. Fresh GPU output
needs visual review before acceptance.

Final round-two CPU checks: 512px/8 samples, all 40 frames; independent saved-clip
audit (including spoke envelopes), provenance and trim reconstruction pass. Atlas
**174,700 bytes at Q80**; H.264/yuv420p, 1600x348, 240 frames, eight seconds.
Stale model, altered grade and CPU-as-GPU rejection checks pass. Wheel pigment
remains pale/flat with tread banding; no PASS. GPU round two remains pending.
