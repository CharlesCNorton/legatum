# Medjay driver round 2

True 3D MPFB anatomy, 53 bones, thick folded linen, headband/feather, convex hide
shield with reverse straps and bronze spear. Fixed rest-camera painting UVs blend
into the original generated unseen-surface fills. Eight AO/curvature bake pairs,
product lighting and one frozen histogram grade remain. All sources and masters
stay outside git; see [SOURCES.md](SOURCES.md).

```sh
tools/art/anim3d/units/medjay/render.sh build
tools/art/anim3d/units/medjay/render.sh finish
tools/art/anim3d/units/medjay/render.sh animate
ROUND=2 tools/art/anim3d/units/medjay/gpu.sh
```

The no-argument executable GPU script requires Cycles Metal and >=64 samples,
renders all stages at 512 px with 256 px copies, publishes reviews/strips/WebPs,
front/top feet checks and an eight-second five-clip H.264/yuv420p video, audits,
packs and validates. Source/code hashes reject stale masters. Technical receipts
never establish art approval. CPU previews use `SAMPLES=8 RESOLUTION=256`.

This round fits complete calf and neck/shoulder surfaces, preserving depth and
weights. Reference alpha runs distinguish calves from the nearby spear; MPFB
hidden helpers are excluded from silhouette measurements. Stone has live contact
shading, grain and source-painted unoccluded lower rim. The clay sheet shows the
finished geometry. Original cage remains editable in the plain master.

Idle/walk/hit/death use Quaternius CC0 motion with reference/rest/roll compensated
Blender constraints. Carrying arms layer open idle; foot rotations are untouched
after retargeting. Root/floor support adaptations are recorded. Only the weapon
attack and equipment release are authored. Cloth is modeled, not simulated.

`app/src/assets/units/anim/medjay.{webp,json}` is an unwired candidate. Version 2
uses logical 160px cells, anchor (84,141), and per-frame `rects` with x/y/w/h/ox/oy.
Reconstruct each trimmed frame before anchoring. All 8/8/10/4/10 frames remain,
full alpha is preserved, quality >=75 and size <=200,000 bytes are enforced.

External root: `~/LegatumRuns/anim-pilot`; sources `assets/medjay`, editable and
512/256 masters `masters/medjay`, reviews `review/3d-v2/medjay-*`. Incoming GPU
evidence is archived under `masters/medjay/driver-r1-gpu`. Exact results and
limitations are in `medjay-log.md`, `audit.json`, `validation.json`, `pack.json`.
No PASS until rest appearance and all five clips meet the painting's quality.
