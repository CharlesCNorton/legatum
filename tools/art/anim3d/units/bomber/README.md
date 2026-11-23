# Bomber — driver round 2 candidate

The aircraft uses closed 3D geometry, frozen painting UVs, image-generated unseen-surface fills, real AO/curvature bakes, product lighting and one measured rest-pose histogram grade. This round follows the successful GPU round-one pass, preserved under `masters/bomber/driver-r1-gpu/`.

Changed: masked cream stone grain and rim pigment with a clean contact footprint; a tilted nose lens and matching solid frames; smaller spinners; original painted propeller highlights and tip bands; generated fills only behind removed blades; a collapsing solid support, stronger wing buckling and a smooth propeller stop. Original paint supplies all other visible colour. All masks are texture coverage, not image cards or geometry substitutes.

Run from the repository root. Every Blender invocation uses the gated `blender` on PATH, one at a time. External inputs and masters remain under `~/LegatumRuns/anim-pilot/`; provenance is in `SOURCES.md`, the asset registry and `app/src/assets/PROVENANCE.md`.

```sh
tools/art/anim3d/units/bomber/render.sh build
RESOLUTION=512 SAMPLES=8 tools/art/anim3d/units/bomber/render.sh all
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/bomber/deliver.py all
# Complete final host GPU pass, including all stages, packing, checks and movie:
ROUND=2 tools/art/anim3d/units/bomber/gpu.sh
```

The executable GPU handoff requires Metal, defaults to 96 samples and 512 px, and never silently falls back. Before rendering it verifies builder, texture and master hashes. It retains a round log/status, reports the transcript path and outcome to the driver, and emits a receipt only after verifying GPU512/256 provenance, geometry, atlas and decoded-atlas MP4. It does not write PASS. `ROUND` comes from the driver. The 160 px trimmed JSON contract is documented in the bomber chapter of `PLAYBOOK.md`.

CPU checks: all 40 clip frames, **197,232 bytes at quality 80**, exact decoded alpha/trim offsets, transparent gutters, fixed anchor and held death pass. Geometry audit passes all five clips, 73 meshes, finished projected surfaces, clean stone contact, stationary base, shaft axes, loop closure, propeller deceleration and wreck contact. There are 64 stage/master PNGs each at 512 and 256 px, including top/front move views. The MP4 is H.264/yuv420p, 1600 × 348, 240 frames and 8.000 s. Six delivery regression tests, eight Python syntax checks and both Bash syntax checks pass. CPU renders use Cycles/8 samples with denoising and remain previews.

At 64 px it reads as the same bomber. At 256 px the stone and glazing are closer; wingtip shape, hub/propeller finish and the still-too-intact wreck remain visibly different from the painting's finish. Large rotations expose the limitations of fixed-view paint. Silhouette IoU is .882 at 256 and .884 at 64; shared opaque-pixel RGB error is 6.166/5.626, versus GPU round-one 9.080/7.831. Different sample counts limit that comparison, and metrics do not establish art parity. **No PASS; this round's GPU rendering and visual acceptance remain outstanding.** No runtime activation is included.
