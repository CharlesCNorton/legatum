# Bomber — round 2 candidate

The editable aircraft is real closed 3D geometry with frozen painting UVs and generated unseen-surface fills. Round 2 seats the dorsal turret, finishes geometry before projection, separates painted illumination from physical lighting, uses unprojected cream limestone, and spins solid propellers about fixed shaft mounts. Source masks prevent the painting's blades from remaining on the body during rotation.

Run from the repository root. Every Blender invocation uses the gated `blender` on PATH, one at a time. External inputs and masters remain under `~/LegatumRuns/anim-pilot/`; provenance is in `SOURCES.md` and the external asset registry.

```sh
tools/art/anim3d/units/bomber/render.sh build
RESOLUTION=256 SAMPLES=8 tools/art/anim3d/units/bomber/render.sh c
source tools/art/anim3d/env.sh
RESOLUTION=256 "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/bomber/deliver.py c
# Complete final host GPU pass, including all stages, packing, checks and movie:
ROUND=2 tools/art/anim3d/units/bomber/gpu.sh
```

The executable GPU handoff requires Metal, defaults to 96 samples and 512 px, and never silently falls back. It retains a round log/status and emits a receipt only after verifying GPU512/256 provenance, geometry, the atlas and decoded-atlas MP4. It does not write PASS. `ROUND` comes from the overnight driver. The 160 px trimmed JSON contract is documented in the bomber chapter of `PLAYBOOK.md`.

Round-2 CPU checks: all 40 clip frames, **192,266 bytes at quality 80**, exact decoded alpha/trim reconstruction, transparent gutters, fixed anchor and held death pass. Geometry audit passes all five clips, 73 meshes, finished projected surfaces, stationary base, shaft axes, loop closure and wreck contact. There are 64 stage/master PNGs each at 512 and 256 px, including the top/front move check. The MP4 is H.264/yuv420p, 1600 × 348, 240 frames and 8.000 s. Five delivery regression tests pass. CPU renders use Cycles/8 samples with denoising and remain previews. Prior round evidence is archived under `masters/bomber/round1-cpu`; this round under `round2-cpu`.

At 64 px it reads as the same bomber. At 256 px the canopy/nacelle geometry, propeller finish and flat-looking stone rim remain below the painting. The death settles but still looks more like a hard landing than a convincing wreck. Frozen painted highlights and unseen-surface seams remain visible under large rotations. Silhouette IoU improved from .847 to .878 at 256 px and .858 to .883 at 64 px; these metrics do not establish art parity. **No PASS; GPU rendering and visual acceptance remain outstanding.** No runtime activation is included.
