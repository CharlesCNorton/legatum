# Bomber — driver round 3 candidate

True 3D aircraft with finished closed geometry, frozen painting UVs, generated unseen-surface fills, actual AO/curvature bakes, product lighting and one automatically measured histogram grade. The incoming round-two GPU pass succeeded; its complete evidence is preserved in `masters/bomber/driver-r2-gpu/`.

Round three adds a generated clean stone top beneath the collapsing support, retains the original painted rim and live contact AO, finishes the support's cap normals and bevels, rounds both wing tips and extends the far wing root. Death folds the outer wing at a span break and retains a thicker support remnant. Settlement and audit now sample evaluated aircraft triangle surfaces against the actual stone/support BVH. A farther-left death path clipped the tail; the original horizontal path was restored and the final death clip rerendered.

All textures color real geometry; alpha never replaces meshes. Generated stone provenance, source hash and exact prompt are in `SOURCES.md`, `stone-fill.json` and `stone-fill.prompt.txt`. External copy: `~/LegatumRuns/anim-pilot/assets/bomber/stone-fill-source.png`. No human/animal motion applies to this aircraft; actual top/front move views check shaft axes and bank.

Run from the repository root. Every Blender invocation uses the gated plain `blender` command, sequentially:

```sh
tools/art/anim3d/units/bomber/render.sh build
RESOLUTION=512 SAMPLES=8 tools/art/anim3d/units/bomber/render.sh all
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/bomber/deliver.py all
blender -b --disable-autoexec --python-exit-code 1 --python tools/art/anim3d/units/bomber/audit.py
# Complete host GPU pass; no arguments, ROUND supplied by the driver:
ROUND=3 tools/art/anim3d/units/bomber/gpu.sh
```

The GPU entry point requires Metal and defaults to Cycles GPU512/96. It verifies builder/texture/master hashes, renders every stage, writes 512/256 masters and interim reviews, refits the rest grade, audits geometry, packs/validates the trimmed atlas and makes the decoded five-clip H.264 movie. The round log/status and receipt record success or failure. The receipt now includes the wreck contact result. No script writes art PASS automatically.

CPU results: all **40 frames**, **197,588 bytes at quality 80**, logical **160 px** cells with per-frame offsets. Decoded alpha, offsets, gutters, clipping margins, current hashes, timing, motion and held death pass. All five geometry audits pass with 73 meshes, fixed base, local propeller axes and periodic loops. The sampled terminal contact gap is zero across 21,240 valid stone-surface samples; this is not a continuous collision proof. Six delivery regression tests pass, including invalidation when either generated fill changes. Nine Python files and both Bash entry points parse. There are 64 PNGs each at 512 and 256 px. The MP4 is H.264/yuv420p, 1600×348, 240 frames, 8.000 seconds.

At **64 px**, the same olive twin-tail bomber reads clearly. At **256 px**, stone and wing contours are closer, but propeller hubs/blade finish, nose glazing edges and the support shape remain distinguishable from the painting. The folded wing improves death, although the wreck still looks too intact and supported near the disc edge. Top views and large rotations reveal fixed-view pigment/fill seams. **No PASS: GPU round-three rendering and visual acceptance remain outstanding.** The static painting stays in use; no runtime activation is included.
