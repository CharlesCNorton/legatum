# Barbarian spearman — round 1

True 3D MPFB body, original kit, 53-bone rig and authored idle/move/attack/hit/death
clips. See the unit's infantry chapter in `../../PLAYBOOK.md` for build commands,
quality method, external assets and the trimmed v2 atlas contract.

Run `tools/art/anim3d/units/barbarian-spearman/gpu.sh` from the repo root for the
complete sequential GPU pass. No arguments. It requires the editable external
masters already produced by this lane under `~/LegatumRuns/anim-pilot/masters/barbarian-spearman/`.
The script explicitly requests Cycles Metal; no silent CPU fallback.

For a serial CPU preview batch under one gate acquisition:

```sh
source tools/art/anim3d/env.sh
RESOLUTION=512 SAMPLES=8 blender -b --disable-autoexec --python-exit-code 1 \
  --python tools/art/anim3d/units/barbarian-spearman/refresh.py
```

`STAGES=c,d,e-attack` can restrict an iteration. A fresh `c` derives a new common
grade; rerender all clips before packing. Each render manifest pins its blend and
grade, each clip pins the source blend, and the pack report pins every frame.

Source painting: project's CC BY 4.0 barbarian-spearman master at
https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/barbarian-spearman-source.png .
MPFB 2.0.18 anatomy/weights are CC0; MPFB software is GPL-3.0-or-later. The linen and
hair back-surface textures reuse the project's CC BY 4.0 generated horseman fills.
`assets.lock.json` pins all external PNG inputs; `assets/SOURCES.md` under the
external animation root records their provenance. No third-party paid asset.

The animation atlas is an art candidate, not runtime integration or art approval.
The target remains the original painting at 256 px and the same identity at 64 px.
Current limitations are recorded in `REVIEW.md` after actual render inspection.

Projection masks exclude the original painting's spear from non-weapon surfaces,
so moving the actual spear does not leave a second painted spear behind. The
excluded band uses the underlying material fill. `projection_mask.py` can refresh
packed masters and preserve their existing animation keys; rerender all textured
stages and regrade/repack afterward.
