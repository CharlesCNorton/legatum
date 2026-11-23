# Bomber — round 1 candidate

Run from the repository root. All Blender work uses the gated `blender` on PATH, one invocation at a time. Downloads, painting, generated fill, editable `.blend` masters, six 512 px AO/curvature maps, frame masters and reviews live under `~/LegatumRuns/anim-pilot/`. `build` reconstructs the original geometry and rebakes, invalidating previous renders.

```sh
tools/art/anim3d/units/bomber/render.sh build
# Individual low-sample preview stage:
RESOLUTION=256 SAMPLES=8 tools/art/anim3d/units/bomber/render.sh c
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/bomber/deliver.py c
# Complete final GPU pass from the saved material master:
ROUND=1 tools/art/anim3d/units/bomber/gpu.sh
```

The GPU command requires Metal and never silently falls back. It writes every stage at 512, retains 256 copies, packs/validates the trimmed 160 atlas and renders the five-clip MP4. It preserves CPU raw renders at other resolutions, but replaces the 512 pass on rerender; save a separate round archive externally if needed. The JSON format is documented in the bomber chapter of `PLAYBOOK.md`.

This is a fixed-view, fully volumetric airframe fitted to the painting, with frozen UV colour, generated underside fill, mechanical pivot animation and crash shape keys. It is not a neutral photogrammetry asset: large rotations reveal projection seams and already-painted highlights. The rest pose is much closer than plain procedural materials, but canopy/turret volume, propeller hubs and stone grading still need refinement. The death has no smoke or debris simulation. No PASS marker or runtime activation is included. A technical pass is not an art approval.

Round-1 local checks: 40 frames retained; candidate atlas **193,478 bytes at quality 80**, logical 160 px cells, all trim offsets reconstruct within bounds. Geometry audit passed five clips, closed-volume principal geometry, fixed base, root/propeller loop closure, measured wreck contact and held terminal pose. All final source frames are 512 px Cycles CPU at 4 samples with denoising, with 256 copies; these are previews, not a GPU sign-off. Python and shell syntax and diff whitespace checks passed. Final GPU settings default to 96 samples.
