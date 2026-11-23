# Round 2 — candidate, not PASS

Opened the complete incoming GPU comparison, detail and clip strips, plus sampled
round-1 MP4 frames before editing. That GPU pass succeeded: 40 frames, 158652 bytes
at quality 90, with six delivery regressions passing. Its original 512/256 masters,
raw frames, blends and reviews are preserved in `masters/reislaufer/driver-r1-gpu/`.
No unit-specific feedback file was present at the start or final check.

Round 2 replaces the thin plume with three closed feather lobes, fits the neck
through inverse skinning, uses garment pigment on covered body faces, adds pinned
image-generated steel/skin fills, and puts grain in the camera-visible stone
shader. Stone tone was calibrated against actual painting patches. Existing
beveled straps, buckles, folded cloth, AO/curvature bakes, product lighting and
frozen histogram grade remain. The source painting and runtime behavior are
unchanged.

The captured death now settles both heels through positional IK without changing
foot yaw. This exposed and fixed a coordinate bug: joint directions, as well as
positions, must be converted to rig space when the character root has rotated.
The audit now rejects a terminal heel more than 3 mm from its support level.

At **256 px**, the neck and plume silhouette are closer to the painting, and the
base is warmer. The feather still lacks the original's intricate edges; the base
rim is too uniform, the shoulder/cuff shapes differ, and the attack exposes a flat
cloth patch below the breastplate. The fallen body is better grounded but still
overhangs the small disc, with visible projection-to-fill transitions. At **64 px**,
the unit's identity, split red/yellow clothing and pike read correctly; the hat and
base remain distinguishable. This does not meet painting parity or five clean
clips. **No PASS file was written.**

Final CPU checks, Cycles 256 px / 12 samples:

- Model build and three actual 512px AO/curvature bake pairs succeeded. All five
  action builds and all review stages rendered, including front/top foot cycles.
- Scene audit passed: 116 finished projected meshes, maximum sampled projection
  error 0 px; 53-bone rig, fixed base, positive scales and held death. Maximum
  checked support-hand error 0.000000248 m. Sampled moving-world stance drift
  0.000000031 m and support-foot yaw 0.02798 degrees. Final heel heights
  0.08499995–0.08499998 m against the 0.085 m support level. These are sampled
  geometry checks, not a continuous collision or visual-quality guarantee.
- Trimmed 160px atlas: **156182 bytes, quality 90, all 40 frames** (8/8/10/4/10).
  Source/render/grade/metadata hashes, exact decoded alpha/offsets, frame bounds,
  motion and held death validate. Six delivery regressions pass.
- Round-2 movie decoded from that atlas: **H.264, yuv420p, 1600x348, 240 frames,
  8 seconds**, all five clips side by side at 2x on cream; ffprobe verified.
- Python/Bash syntax and whitespace checks pass. No Rust, WASM or app code changed.

The updated `b/c/d/e/f/g` images, five clip WebPs, decoded atlas review, audit,
validation and movie are in `~/LegatumRuns/anim-pilot/review/3d-v2/reislaufer-*`.
Current editable blends, bakes and 256px masters are in `masters/reislaufer/`.
Round-2 512px masters require the GPU pass; the prior GPU masters remain archived.

From the repository root, the lead must run:

```sh
ROUND=2 tools/art/anim3d/units/reislaufer/gpu.sh
```

This executable no-argument handoff requires Metal Cycles, rebuilds and renders
all stages at 512, retains 512/256 masters, packs the 160px atlas, regenerates the
rest comparison and movie, and runs validation/regressions before a GPU receipt.
It never grants visual approval or writes PASS automatically.

Git staging was attempted, but the sandbox denied
`.git/worktrees/lane-23/index.lock`; the runner must commit the changes. No push or
PR was made. The branch contains the currently available `origin/master`
(zero missing commits; no fetch performed).
