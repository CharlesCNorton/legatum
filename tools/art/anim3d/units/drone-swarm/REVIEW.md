# Drone swarm — driver round 2

Not art-approved; no PASS marker. The supplied round-1 GPU pass succeeded at
512 px / 96 samples. Its images, movie, receipt and masters are archived under
`masters/drone-swarm/driver-r1-gpu/`. This revision was checked with Cycles CPU
at 512 px / 8 samples; the updated GPU handoff still needs to run on the host.

At 256 px the cream stone and projected paint are close. Wider lower hulls,
thicker near struts, hidden far supports, tapered solid rotor spars and adjusted
blades improve the outline. Muted generated brass removes the orange seams.
The blade shapes, hull shoulders, arm contours and gimbal profile still differ
from the painting. At 64 px the formation and identity match, but the contours
remain distinguishable. The rest-pose acceptance bar is not met.

Rest silhouette IoU at alpha >128 improved from .8060 to **.8301** overall and
.6609 to **.7048** for drones. Base IoU is .9670. These are overlap measurements,
not art approval. All c/f/detail, plain, pose, five clip strips, front/top move
views, decoded atlas and four encoded MP4 contact frames were visually inspected.

The new triangle audit exposed real lower-drone intersections hidden by the
orthographic view. Separate flight depths retain the painting registration.
Staggered descent prevents the upper drone catching the lower ones; three
separate terminal wrecks replace the crowded pile. The terminal pose is clearer,
but blade sampling still looks stepped and the crash feels like a controlled
landing. These remain visual weaknesses for the next pass.

## Checks and outputs

- Geometry audit passes: 163 solid meshes, frozen UVs on finished surfaces,
  camera-only pigment, six real AO/Pointiness bakes, stationary base, rest-matching
  clip entries, closed root/gimbal loops, and grounded held death.
- Zero inter-drone triangle intersections across all **40 sampled poses**.
  This does not prove continuous collision freedom, containment without surface
  crossings, or intra-drone joint clearance.
- All five clips: **8/8/10/4/10**, transparent 512 and 256 px masters.
- Trimmed 160 px atlas: **180,000 bytes, WebP quality 85**. Exact decoded alpha
  and per-frame offsets; final two death frames share an identical rectangle.
- Six delivery/provenance regression tests pass, including changed build-input
  rejection, corrupted offset/atlas rejection and CPU-as-GPU rejection.
- MP4: H.264, yuv420p, **1600 x 348, 240 frames, 8 seconds**, decoded atlas at 2x.
- Ten Python files parse; both shell scripts pass `bash -n`; `git diff --check`
  passes. No engine, UI, rules or runtime changes.

The broader static gate on committed HEAD passed hygiene and public-claims;
the art gate could not render its sets (`render-sets.mjs` exited 1). It did not
check the uncommitted edits. Git staging/commit was attempted with the required
coauthor but denied at `.git/worktrees/lane-23/index.lock`; changes remain for
the runner to commit. No push, merge or PR. `origin/master` is already included.

The GPU script now checks sealed build inputs before launching Blender and runs
the new collision audit plus delivery regressions. The receipt includes both
build inputs and collision results. GPU512 provenance is checked for every stage.

```sh
ROUND=2 tools/art/anim3d/units/drone-swarm/gpu.sh
```

This no-argument executable renders all stages on Metal Cycles at 96 samples,
keeps 512/256 masters, rebuilds the trimmed atlas, gallery and round movie,
validates them and records a receipt. No new GPU success is claimed from CPU
previews. The runtime continues to use the original painting.
