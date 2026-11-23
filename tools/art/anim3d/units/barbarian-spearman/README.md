# Barbarian spearman — round 2

True 3D MPFB body, original kit, 53-bone rig, CC0 Quaternius idle/move/hit/death and an original spear attack.
Rest/roll calibration preserves source foot rotations; the top/front feet sheet
checks the full move cycle. See the unit's infantry chapter in `../../PLAYBOOK.md` for build commands,
quality method, external assets and the trimmed v2 atlas contract.

Run `tools/art/anim3d/units/barbarian-spearman/gpu.sh` from the repo root for the
complete sequential GPU pass. No arguments. It requires the editable external
masters already produced by this lane under `~/LegatumRuns/anim-pilot/masters/barbarian-spearman/`.
The script explicitly requests Cycles Metal; no silent CPU fallback.

For a serial CPU preview batch under one gate acquisition:

```sh
source tools/art/anim3d/env.sh
RESOLUTION=256 SAMPLES=8 blender -b --disable-autoexec --python-exit-code 1 \
  --python tools/art/anim3d/units/barbarian-spearman/refresh.py
```

`STAGES=c,d,e-attack` can restrict an iteration. A fresh `c` derives a new common
grade; rerender all clips before packing. Each render manifest pins its blend and
grade, each clip pins the source blend, and the pack report pins every frame.

Source painting: project's CC BY 4.0 barbarian-spearman master at
https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/barbarian-spearman-source.png .
MPFB 2.0.18 anatomy/weights are CC0; MPFB software is GPL-3.0-or-later. The linen and
hair back-surface textures reuse the project's CC BY 4.0 generated horseman fills.
Additional fur/leather fills reuse original barbarian archer imagegen artwork.
`SOURCES.md` records every source; `assets.lock.json` pins all external PNG inputs; `assets/SOURCES.md` under the
external animation root records their provenance. No third-party paid asset.

The animation atlas is an art candidate, not runtime integration or art approval.
The target remains the original painting at 256 px and the same identity at 64 px.
Current limitations are recorded in `REVIEW.md` after actual render inspection.

Frozen projection samples the finished 3D surface. Rest-camera visibility tests
exclude parts hidden by independent equipment. The source spear's narrow band
uses feathered adjacent painted pigment samples, so the real spear can move
without leaving another shaft on the clothes. These are shader masks, not alpha
cutouts or source-image edits. Rebuild paint, bakes and all clips after changes.

The GPU script writes the driver's `barbarian-spearman-round${ROUND}.mp4` after
reconstructing decoded atlas crops at their per-frame offsets. It verifies all
40 samples, lossless alpha, size/quality, the identical death hold, and the
8-second H.264/yuv420p movie. It records a transcript and explicit failure stage.
CPU256 iteration uses `pack.py --preview`; it never claims current GPU512 masters.
