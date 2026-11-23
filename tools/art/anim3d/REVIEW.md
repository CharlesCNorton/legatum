# Spearman review — round 9 motion fix

**Not PASS against the painting yet.** The walk now uses a complete open action,
points forward when supporting weight, and has measured heel/toe contact through
heel strike, toe-off and the loop boundary. It still reads as a slightly stylized
march. At 256 px, face/shield/foot proportions and pale surfaces exposed during
hit/death remain distinguishable from the painting. At 64 px it clearly reads as
the same spearman. No `spearman-PASS` was written.

## Diagnosis and change

Round 8 reconstructed only CMU leg directions, overwrote foot directions, and
screen-fitted/lifted the feet along the camera ray. That discarded captured roll
and embedded splay in the fitted geometry. Sandals were rigid ankle children,
so even correct ankle rotation could not reproduce toe flex.

The replacement imports the pinned CC0 Quaternius Standard library through
Blender and samples native world-space Copy Rotation constraints with complete
rest/reference offsets. MPFB's spread-leg rest is matched to the source T-pose;
roll is retained. Blender's pose-to-local conversion bakes sampled parent
matrices, avoiding stale-parent transforms. No foot angle is authored after
retargeting. The actual finished sandals and straps now bend on foot/ball bones,
while retaining their neutral surface and the original MPFB body/53-bone rig.

- Idle: `Idle_Loop`, with a reference offset into the weapon guard.
- Move: `Walk_Loop`, with open idle arms layered through Blender NLA for carrying
  the spear/shield. Source pacing is retained at 1.33 seconds per cycle.
- Hit: `Hit_Chest`, with a final transition back to the same idle.
- Death: `Death01`, with an 18% entry transition out of the guard. Source joint
  motion remains intact; the armoured body is grounded against the raised disc,
  and an invisible thick collider supports cloth outside it. This needs up to
  180 mm of body-root lift for the armour/disc; it is not the walk contact solve.
- Attack: original weapon-specific keys, with planted controls rebased on idle.
  Weapon release and sliding the grip along the shaft remain accessory handling.

Motion sources, versions, hashes and licences are in `units/spearman/SOURCES.md`
and external `assets/SOURCES.md`. No Mixamo, paid assets, accounts or uploads.

## Verification

All new images are explicitly **CPU Cycles previews, 256 px / 8 samples**.
The top/front feet views use 192 px cells / 8 samples. Opened the rest comparison,
all five strips and the feet sheet at 256/64 px. Animated WebP strips exist.

- Final geometry audit: **40 samples, zero findings**, covering camera bounds,
  disc/ground intersections, spear crossings, grip, baked cloth and entry/exit
  arm continuity for attack/hit plus death entry.
- Walk: **33 dense frames, 38 supporting-foot samples**, including toe-off and
  wrapped stance. Maximum planted heading **2.397 degrees**, readable horizontal
  footprint heading **4.052 degrees**, actual heel/toe drift **0.0022 mm** after
  virtual travel compensation, support-height error **0.869 mm**, zero positional
  loop seam. Virtual speed: **1.07334 m/s**.
- Corrections stay small: root XY **27.2 mm**, native two-bone foot IK **23.4 mm**,
  vertical sole contact **29.9 mm**. Retargeted foot rotation is preserved by a
  native world-space rotation constraint during IK.
- The metric retains raw airborne yaw. A nearly vertical toe-down foot projects
  less than 8 cm onto the ground, making horizontal yaw ill-conditioned; these
  samples are labelled raised and are not used as a planted-foot heading test.
  Ankle travel while the foot rolls is also reported separately from sole slip.
- Scene checks pass original **19,158 body vertices / 53 bones**, 314 painted
  materials, 280 unseen fills, articulated sandal weights, shared cream base,
  calibrated camera and all twelve shield-relief clearances.
- CPU preview packing: **182,334 bytes, quality 80**, trimmed 160 px cells, all
  **8/8/10/4/10** frames. Independent decoding passes source hashes, timing,
  offsets, exact alpha, gutters, bounds, motion and byte-identical held death.
  This preview is external in `masters/spearman-3d-v2/round9-cpu-atlas/`;
  the shipped atlas is reserved for the driver's GPU pass.
- **2 pipeline regression tests pass**. Changed Python/Bash syntax and public
  hygiene pass; `git diff --check` passes.
- The repository-wide art distinctness gate could not launch Chromium in this
  sandbox: macOS `bootstrap_check_in ... Permission denied (1100)`. It did not
  produce an art verdict. Full error: `spearman-round9-art-gate.txt` in review.

Exact current motion results: `review/3d-v2/spearman-motion-checks.json`.
CPU delivery validation: `review/3d-v2/spearman-round9-cpu-delivery/`.
Round-8 masters, clips and renders remain in
`masters/spearman-3d-v2/round8-preserved/`.

## GPU handoff

From the repository root, on the GPU host:

```sh
ROUND=9 tools/art/anim3d/units/spearman/gpu.sh
```

The executable verifies GPU availability and pinned motion assets, rebuilds the
master and all five clips, renders every stage at 512 px on Cycles GPU, checks
and renders the feet, exports 512/256 masters, packs and validates the trimmed
160 px atlas, and writes `spearman-round${ROUND}.mp4`: all five decoded clips,
eight seconds, 2x on cream, H.264 yuv420p. It also writes the rest comparison and
stage/status receipts. It never awards PASS automatically.

Final GPU size/quality and visual approval remain pending. No Rust, game rules,
WASM or UI runtime changed. No push, PR or master merge is part of this round.

Git staging was blocked by the sandbox (`index.lock: Operation not permitted`).
Sixteen changed/new files remain for the runner to commit. The requested
gpt-6-astra co-author trailer is included in external
`review/3d-v2/spearman-round9-commit-message.txt`.
