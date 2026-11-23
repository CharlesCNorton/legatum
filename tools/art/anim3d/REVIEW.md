# Spearman review — round 4

**Not PASS.** This is a CPU-rendered art candidate; the game still uses the
painting. At 256 px the render remains distinguishable from the painting. At
64 px it reads as the same gold/red/cream spearman, but stance and base still
differ. The sleeve/shoulder transition, foot shape, base shading and projection
stretching during larger poses need another art pass.

## What changed

The shield's real boss and twelve raised rays now align with the painted
ornament. Each relief vertex is seated on the convex shell with a ray
intersection and explicit raised depth: moving decoration sideways without
correcting depth had buried it, which the plain-material review caught.
The competing old shield-paint layer is disabled. Frozen projection coverage
under the relief is continuous; the painting's illumination supplies 96% of
fully covered surfaces and physical shading supplies 4%. Existing generated
bronze/wool/linen/leather fills remain packed for unseen surfaces.

The volumetric crest is narrower; the right-side ankle is moved inward/back,
and the real feet turn outward before projection to reduce pale base colour
leaking onto sandals. Fine grain and restrained specular response improve the
physical cream base. Death retains shoulder pins but softens lower-cape pins,
removing the rigid triangular shelf; released shield transforms retain scale.
All five clips and cloth caches were regenerated from the corrected master.

The executable `units/spearman/gpu.sh` performs the complete host pass. New
`units/spearman/delivery.py` packs trimmed 160px frames, validates their decoded
offsets/alpha, exports genuine 512/256 GPU masters, and makes the eight-second
five-column movie. JSON v2 is documented in the infantry PLAYBOOK chapter.
Older fixed-grid tools remain available for old callers, but are not this
unit's current handoff. Review image/movie captions identify CPU previews.

## Exact checks

- CPU Cycles: 256px / 12 samples, fixed camera and one frozen histogram grade.
- Atlas: **198,130 bytes, quality 85, 40 frames**, 160px
  untrimmed canvas with per-frame crop offsets. SHA256
  `5f2180633ff1136d362fcf6ff46ecf15127fb381f7098b2210f62af51cc13148`.
- Decoded validation: PASS for current source/grade hashes, clip metadata,
  crop bounds, gutters, exact reconstructed alpha, camera margins, motion,
  size and quality. Held death source PNGs are identical bytes and pixels.
- Saved-rig audit: **40 samples, zero findings**. Original 19,158 body vertices
  and 53 bones, persistent cloth, stationary cream base, floor/camera bounds,
  grip and spear centerline clearance pass. This is not a full collision solver.
- **2 regression tests pass**; syntax passes for **23 Python, 3 Bash, 2 JSON**
  files. Working-tree hygiene: **31 text files, zero findings**. Diff whitespace
  passes. No Rust, rules, app runtime or WASM changed.
- Movie: H.264 yuv420p, **1600 × 352**, **192 frames**, **24 fps**, **8 seconds**;
  all five decoded clips shown simultaneously at 2x, verified with ffprobe.
- Rest silhouette IoU: **0.8511**, versus received round 3
  **0.8394**. RGB error on the union: **33.54 / 38.35 / 39.69**, versus
  **35.58 / 41.26 / 42.70**. These are diagnostics, not art approval.

## Evidence and GPU handoff

`ANIM_ROOT/review/3d-v2/` contains updated b/c/details/d/e review images,
`spearman-f-restpose-compare.png`, decoded-atlas preview, `spearman-round4.mp4`,
`spearman-log.md` and `spearman-final-report.json`. Received round-3 evidence is
preserved in `spearman-round3-preserved/`; the old editable master is preserved
outside git. The requested prior running log, round-3 GPU log and gpu.sh were
absent at round-4 start. The received render manifests said CPU; a round-3 GPU
success could not be verified.

Run from the repository root on the GPU host:

```sh
ROUND=4 tools/art/anim3d/units/spearman/gpu.sh
```

This requests Cycles GPU/Metal at 512px / 64 samples, all stages and clips,
validation, the comparison images and movie. It exports 512/256 masters under
`ANIM_ROOT/masters/spearman/`; the editable source and caches remain under
`masters/spearman-3d-v2/`. Those final GPU renders/exports have **not** run in
this sandbox. GPU validation and visual review remain pending. The script
never writes PASS automatically. The lead still owns browser/art review before
integration; no push, merge, PR or deployment is part of this task.

## Runner commit

Git staging failed because the sandbox could not create this worktree's
`index.lock`; changes remain uncommitted for the runner. The branch already
contains the available `origin/master` (zero missing commits); no fetch, push
or merge was attempted. Suggested commit message:

```text
Refine spearman relief and deliver trimmed animation atlas

Co-Authored-By: gpt-6-astra (Codex) <noreply@openai.com>
```
