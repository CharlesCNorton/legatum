# Mounted candidate — 22 November 2026

Delivery exists, but the art does **not** meet the painting-quality approval bar.

- 256 px: recognizable bay horse and ivory-clad rider, painted surfaces, warm stone,
  Greek-key blanket and bronze kit. Horse anatomy remains stylized and angular;
  mane/tail need volume, cloth needs better folds, and tack/reins need refinement.
  Painting projection is approximately registered and contains baked lighting.
- 64 px: reads as the same unit type, but the upright/narrow silhouette and wider
  base differ visibly from the painting. Higher GPU samples cannot fix that.
- Motion: source horse trajectories drive the canter; attack couches/thrusts the
  spear; hit recoils; death collapses to the side with the rider slumped and spear
  released. Tack intersections and physical plausibility still need art review.

## Verified CPU delivery

Cycles CPU, 8 samples, 3 threads, all Blender work through the machine-wide gate.
Atlas: **198,252 bytes**, quality **60**, 16 alpha levels, 2560×1280, 40 frames in
8/8/10/4/10 rows, transparent 256 px cells, anchor (127,221).

- `mounted/audit.py`: five clips passed; no reported errors. Checks both rigs,
  saddle parent, fixed base, height bounds and held terminal geometry. Canter has
  one unsupported sample out of eight (maximum two).
- `mounted/validate.py`: passed dimensions, metadata, all 40 frames, transparency,
  padding, motion, byte cap, frame margins and held terminal pixels/silhouettes.
- All 18 Python sources compile; both render shell scripts pass `bash -n`;
  `git diff --check` passes. No Rust or runtime UI code changed.

These checks establish the delivery contract, not artistic approval or complete
collision detection. No sandbox Metal render was attempted.

## Review and source files

External root: `~/LegatumRuns/anim-pilot/`.

- `review/3d-v2/horseman-f-restpose-compare.png`: painting/rest/split/crossfade.
- `review/3d-v2/horseman-packed-review.png`: original, raw rendered and decoded
  delivery frame at native 256 and 64 px.
- `review/3d-v2/horseman-e-*-strip.png` and `.webp`: all clips.
- `review/3d-v2/horseman-{pack,validation,rig-audit}.json`: exact output evidence.
- `masters/horseman-3d/horseman.blend` and `clips/*.blend`: editable packed masters.
- `assets/SOURCES.md` and `mounted/assets.lock.json`: licences and pinned inputs.
- `assets/horseman/painted-fills.png`: generated unseen-surface fills; exact prompt
  is `mounted/painted-fills.prompt.txt`. These fills are packed in the masters.

## Lead GPU render

Run from the repository root on the host with Metal access. All calls retain the
shared gate. Render the rest first to recalibrate the common grade, then every clip.

```sh
export UNIT=horseman RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES=64
for stage in c d e-idle e-move e-attack e-hit e-death; do
  tools/art/anim3d/render.sh "$stage"
done
RESOLUTION=512 tools/art/anim3d/render.sh c-details
source tools/art/anim3d/env.sh
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/mounted/pack.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/mounted/validate.py
```

Reinspect the GPU comparison and decoded atlas; the CPU byte count is not a
promise about the future GPU export. The packer refuses output above 200,000 bytes.

## Runner handoff

Git merge and staging were attempted, but the sandbox denied `ORIG_HEAD.lock`
and `index.lock` in `.git/worktrees/lane-4`. Nothing was committed or pushed.
The runner must merge the already-fetched `origin/master`, resolve if necessary,
then run the requested post-merge determinism and pin tests before committing:

```sh
tools/sim/build-slot.sh -- cargo test -p legatum-sim --profile release-checked --test determinism
tools/sim/build-slot.sh -- cargo test -p legatum-sim --profile release-checked --lib pinned
```

The prepared commit message is external
`review/3d-v2/horseman-commit-message.txt` and includes the requested co-author line.
