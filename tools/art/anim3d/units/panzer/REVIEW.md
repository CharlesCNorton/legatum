# Panzer, round 1

**Candidate; not passed.** CPU Cycles previews at 256px, 4–8 samples, were inspected
beside the painting at 256px and 64px. Saved stages are in
`~/LegatumRuns/anim-pilot/review/3d-v2/panzer-*`. The first plain sheet is retained
as the first build's immediate evidence; the GPU handoff regenerates it from the
current plain master. All editable scenes and texture bakes are external under
`masters/panzer/`.

At 64px this reads as the same sand/olive, skirted panzer with a long gun. At 256px
it retains much of the original camouflage and painted wear, but is not hard to
tell from the painting. The cupola is too small/low, the gun slope differs, and
the front running gear and fenders extend beyond the painted silhouette. Physical
wheels have less painted richness than the source. The painting projection is
not visibility-baked: some source details can repeat on occluded surfaces and
become visible during movement. Large viewpoint changes expose this strongly.
The first move video exposed source-wheel fragments rotating around mismatched
axles; rotating wheels were removed from projection before final delivery.

The mechanical direction is correct (+X tank travel, -X belt contact travel,
wheel angle = distance/radius). This is an anchored treadmill preview, not a
translating tank driving over a static base. A perfectly invisible wheel loop
seam has not been established. The terminal wreck darkens and holds, with a small
smoke plume; the plume still needs a more natural broken silhouette. Low-sample
CPU smoke is noisy. No `panzer-PASS` has been written.

Validation covers all 40 frames, logical 160px size, trim reconstruction, offsets,
clip order/fps/loops, byte/quality limits, motion, exact terminal death hold,
scene/source hashes, stationary base, bounds and nonzero scales. Two numerical
track tests cover closure, constant speed, tangents and lower-run direction.
Shell syntax and Python compilation were checked. `video.py` verifies the actual
encoded H.264/yuv420p, 1600x348, 240-frame, 8-second MP4 and decodes sample frames.
Current byte/quality and renderer facts are in the external `panzer-validation.json`
and `panzer-pack.json`, not inferred from an old atlas.

The host must run:

```sh
ROUND=1 tools/art/anim3d/units/panzer/gpu.sh
```

That renders all stages with Metal Cycles, creates actual 512px/256px master sets,
rebuilds/validates the atlas and all review images including rest comparison and
track check, and writes `panzer-round${ROUND}.mp4`. This CPU-only round does not
claim a completed GPU pass or real 512px final masters. No runtime code changed.
The next round should register wheels/skirt edges/cupola to measured painting
landmarks, improve projection occlusion masks and hidden fills, and retest wheel
rotation and the loop seam before refining smoke.

Final CPU candidate: **195,132 bytes, WebP quality 85**, all 40 frames in a
1372x572 trimmed atlas. Repository art gate was attempted on HEAD and failed when
`node tools/art/render-sets.mjs` exited 1; it does not establish a candidate pass.
Git staging is blocked by `.git/worktrees/lane-24/index.lock: Operation not
permitted`, so the runner must commit the changes with the requested co-author.
