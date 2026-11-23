# Spartan hoplite — resumed driver round 2

**No art PASS.** At 256 px the swept crest, stance and warm stone are closer,
but helmet/gaze, neck/shoulder drape, linen layering and skin detail still differ
from the painting. At 64 px the red crest, lambda shield and bronze/linen identity
read correctly, but the silhouette and surface finish remain distinguishable.
The five clips are now based on proven open actions plus the weapon attack;
source-paint stretching during movement and the death landing's relation to the
back of the disc still need GPU visual review. Technical success is not art approval.

This pass reshapes the original solid crest tufts and saddle, fits the right
ankle rest stance, mantle and single rounded brooch, preserves painted highlights
through visibility/alpha masks, and grades both stone materials. It retains MPFB
anatomy/weights, physical kit/bevels/straps/folds, AO/curvature bakes, generated
unseen linen, product lights and the single automatic rest-derived RGB grade.
Rest alpha-threshold silhouette overlap improved from **0.770109 to 0.787439**;
this is a contour metric, not an exact-viewpoint or visual-parity claim.

Quaternius CC0 Idle_Loop, Walk_Loop, Hit_Chest and Death01 now drive the body,
with calibrated reference/rest matrices and bone rolls. Walking feet receive no
post-retarget orientation edits. Death releases the held guard into anatomical
source motion; hit samples the source reaction forward/back to recover. Worn-kit
and cloth contact, an independent released-spear trajectory, and shaft support
corrections keep the equipment inside the fixed camera. Only attack/release and
contact constraints are authored. Unit SOURCES.md and assets.lock.json record
provenance; the central art provenance row is updated.

Final CPU evidence (Cycles, 256 px, 12 samples):

- All 40 RGBA frames, counts **8/8/10/4/10**, and all b/c/d/e/f review sheets.
- Actual top/front eight-frame foot views. Four measured planted intervals:
  maximum virtual-ground error **0.00000072 m**, support yaw **0.000053 degrees**.
  Yaw labels on near-vertical swinging feet can flip 180 degrees; support samples
  and the actual rendered soles are the relevant forward-direction evidence.
- Trimmed **160 px**, **172,902-byte WebP at quality 85**, with per-frame offsets.
  Count, alpha/RGB reconstruction, motion, margins, hashes and held-death checks pass.
- Full forty-sample rig/equipment/cloth audit: **0 findings**. Scene/input checks:
  **173 projected meshes, 19,158 anatomical vertices, 53 bones**, nonzero scales.
- Decoded atlas movie: **H.264/yuv420p, 1600×348, 240 frames, 8 seconds**.
  All five strips and extracted final movie frames were opened and inspected.
- All **19 unit Python files** parse; both shell scripts pass `bash -n`; executable
  GPU entry point and `git diff --check` pass. Current-file hygiene: **27 files,
  0 findings**. Public-claims gate passes. No Rust/UI runtime changes were made.
- The GPU master gate correctly rejects this CPU set as missing fresh 512 masters.
  Fresh GPU output and the lead's art review remain outstanding.

External artifacts:

- Editable master, clips/caches, raw renders, 256 gallery and reports:
  `~/LegatumRuns/anim-pilot/masters/spartan-hoplite/round3-3d/`.
- Previous completed GPU512/64 masters remain in `round2-3d/`; prior GPU review
  images/movie are preserved under `review/3d-v2/spartan-hoplite-round1-gpu-preserved/`.
- Updated PNG/WebP review sheets, feet check, round2.mp4 and running log:
  `~/LegatumRuns/anim-pilot/review/3d-v2/spartan-hoplite-*`.

The executable, no-argument lead handoff is:

```sh
ROUND=2 tools/art/anim3d/units/spartan-hoplite/gpu.sh
```

It rebuilds from the preserved unpainted checkpoint, checks inputs, bakes/audits
all clips, renders all stages at Cycles GPU512/64, keeps actual 512/256 masters,
renders the top/front feet checks, verifies GPU provenance, packs/validates the
atlas and encodes/verifies the movie. Output is now teed into both the driver's
log and its retained transcript; the earlier outer log was empty due to redirection.
It fails explicitly without Metal and never creates PASS automatically.

A useful retarget lesson: a carry-pose offset that works for walking can prop up
a death pose. Compare the original donor and blend out of the weapon guard into
anatomical calibration; passing intersection checks alone does not catch that error.

Git staging was denied creating `.git/worktrees/lane-15/index.lock`; changes
remain uncommitted for the runner. The requested co-author message is saved in
`~/LegatumRuns/anim-pilot/tmp/spartan-driver-round2-commit.txt`. No push or PR.
