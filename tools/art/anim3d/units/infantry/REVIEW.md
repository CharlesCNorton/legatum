# Infantry round 1 — CPU candidate, not art approved

Built MPFB anatomy and the 53-bone rig, full-depth infantry kit, frozen painting
UVs, generated unseen-surface fills, actual helmet/jacket AO and curvature bakes,
and five editable actions. Idle/walk/hit/death use Quaternius CC0; the grenade
throw and equipment release are authored. All prescribed stage sheets, five
animated WebPs, rest split-screen and front/top feet review exist under external
`review/3d-v2/infantry-*`. Earlier clip sheets are retained in
`infantry-round1-firstpass/`. Editable blends, maps and genuine 256 px output
remain in `masters/infantry/`.

Observed checks, 2026-11-23:

- CPU Cycles build, projection/bakes, all five animation builds, 44 clip/rig-pose
  images, rest/plain renders and sixteen feet views: exit 0. Main renders are
  256 px, 8 samples; feet are 160 px, 6 samples. No GPU pass is claimed.
- Structural audit: 53 bones, anatomical mesh, current source hashes, stationary
  base, nonzero object scales. Maximum sampled walk toe yaw: **12.39 degrees**
  from forward. Four fully planted ankle intervals: maximum virtual-ground
  drift **2.71e-7 m**; minimum walk sole height **0.086 m**, above the .085 m
  contact plane. These are sampled ankle/contact checks, not a complete friction
  or all-mesh collision solver.
- Candidate atlas: **167,978 bytes**, quality **90**, **785×739** packed pixels,
  160 px logical cells, all **40** frames. Independent decoded validation passes
  trim offsets, lossless alpha, bounds, current hashes, motion in every clip and
  exact held death. The initial pack rejected the walk's top-edge margin;
  the camera was widened and every dependent stage rebuilt before delivery.
- `infantry-round1.mp4`: **8 seconds**, **240 frames**, **1600×348**, H.264,
  yuv420p, five decoded clips side by side at 2x on cream, CPU-labelled. ffprobe
  checks pass; a decoded movie frame was visually inspected.
- Python compile, shell syntax and `git diff --check`: pass. The GPU receipt
  verifier was tested to reject CPU output. GPU execution remains untested here
  because the sandbox has no Metal. The complete script must run on the host.

Visual verdict: **not PASS**. At 64 px this reads as the same olive-uniform,
raised-grenade infantry with an upright rifle. At 256 px the painting is richer
and more natural: the cheek/helmet projection, supporting sleeve, jacket/pouch
silhouette and lower legs need closer fitting; the rim is too dark; newly exposed
surfaces and joints look less painted. The throw is stiff, hit recovery needs
review, and the death deformation is still awkward despite fixing the floating
stance and rifle pivot. Do not replace the game's static art or write a PASS
marker on the strength of technical checks alone.

The host must run, from the repository root:

```sh
ROUND=1 tools/art/anim3d/units/infantry/gpu.sh
```

That no-argument script verifies Cycles Metal GPU, rebuilds/bakes and renders all
stages, creates genuine 512 and 256 masters, regenerates the atlas/JSON, audits,
validates, renders feet views, writes the round MP4 and checks the GPU receipt.
The 512px masters are pending that GPU run; no CPU preview was upscaled or
mislabelled. Review its output before the next round. It never writes PASS.

Git commit attempt was blocked by sandbox permission on `.git/worktrees/lane-18/index.lock`. Changes remain uncommitted for the runner. No push or PR was attempted. `origin/master` was already an ancestor of this branch; no fetch or merge was needed.
