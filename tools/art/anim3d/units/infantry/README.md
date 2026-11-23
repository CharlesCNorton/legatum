# Infantry round 1

Run from the repository root. Assets, previews and masters stay outside git in
`~/LegatumRuns/anim-pilot/`; source pins and licence details are in `SOURCES.md`.

```sh
RESOLUTION=256 SAMPLES=8 tools/art/anim3d/units/infantry/render.sh build
tools/art/anim3d/units/infantry/render.sh animate
tools/art/anim3d/units/infantry/render.sh preview
tools/art/anim3d/units/infantry/render.sh feet
tools/art/anim3d/units/infantry/render.sh pack
ROUND=1 tools/art/anim3d/units/infantry/gpu.sh
```

`gpu.sh` is the single no-argument lead handoff: Cycles Metal GPU, all stages,
512/256 masters, trim/pack/decode validation, feet views and the eight-second
five-clip MP4. It refuses CPU fallback and leaves art approval pending.

The geometry remains volumetric and articulated: MPFB human/53-bone rig,
full-depth olive jacket/trousers, netted helmet, thick webbing/pouches, gaiters,
boots, rifle and released grenade. `plain.blend` retains the unprojected stage;
`infantry.blend` packs frozen painting UVs, generated hidden-surface fills, and
actual baked AO/Pointiness maps. Four clips retarget CC0 Quaternius through
Blender's rest/reference-pose constraints; only the grenade throw is authored.

JSON v2: a 160×160 logical cell and anchor, with each clip's `rects` containing
`x,y,w,h,ox,oy`. Select the atlas rect and paste at `ox,oy` before applying the
cell anchor. Clip rows retain idle/move/attack/hit/death order and 8/8/10/4/10
frames. WebP quality never falls below 75; delivery refuses >200,000 bytes.
This candidate does not change the app renderer. A small atlas is not art approval.

See external `review/3d-v2/infantry-log.md` and the committed `REVIEW.md` for
observed results, remaining defects and exact validation status.
