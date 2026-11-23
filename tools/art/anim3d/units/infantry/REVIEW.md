# Infantry driver round 2 — CPU candidate, not art approved

The round-one GPU pass completed: 166,516 bytes at quality 90. Its review images,
decoded movie frames and genuine 512px masters were inspected before editing and
preserved in external `masters/infantry/driver-r1-gpu/`. The empty driver log was
caused by the internal redirect; `gpu.sh` now tees output to both logs.

Round two replaces separate elbow/knee tubes with continuous weighted folded
cloth (.006m thickness), refits supporting arm/helmet/backpack/rifle/boot volumes,
uses cloth beneath covered anatomy and generated painted skin on exposed parts,
and corrects the bootlace fitting bug. Warm stone grain/live AO and feet-free
lower-rim painting improve the base; reduced sheen/rim strength limits blue fabric.
Hit returns to guard; death blends into the licensed source motion. The four open
clips remain Quaternius CC0 with rest/roll compensation and untouched foot rotations.

Observed checks, 2026-11-23:

- CPU Cycles build/projection/AO/Pointiness, five animation builds, 46 main-stage
  frames (256px, 12 samples), and 16 feet views (160px, 12 samples): exit 0.
- Structural audit passes: 53 bones, anatomical mesh, current input/master/clip
  hashes, weighted thick sleeves/trousers, stationary base, nonzero object scales.
  Walk toe angle max **12.39 degrees**; four planted ankle intervals have max
  virtual-ground drift **2.70948e-7m**; minimum sampled sole Z **0.086m** above the
  **0.085m** contact plane. These are sampled checks, not a full collision solver.
- Candidate atlas: **163,336 bytes**, quality **90**, **789×740**, **40 frames**,
  trimmed **160px** logical cells. Pack and independent decode validation pass
  offsets, bounds, lossless alpha, current hashes, motion and exact held death.
- `infantry-round2.mp4`: **8 seconds**, **240 frames**, **1600×348**, H.264/yuv420p,
  all five decoded clips at 2x on cream. ffprobe passes; decoded frames inspected.
- Python syntax, shell syntax and whitespace pass. Negative checks reject changed
  build inputs and CPU output presented for a GPU completion receipt.

Visual verdict: **not PASS**. At 64px this is recognizably the same grenade-raising
olive infantry; source silhouette differences remain. At 256px the stone and
joint continuity improve, but the shoulder/webbing/pouch contours, forward-facing
right boot, thin rifle, and exposed unprojected material still miss the painting.
The throw is stiff and the death pose remains awkward. Five clips are delivered
for review; they are not certified clean or indistinguishable from the painting.
No PASS marker was written. No runtime loader or game rules changed.

Lead GPU command, from repository root:

```sh
ROUND=2 tools/art/anim3d/units/infantry/gpu.sh
```

This rebuilds/bakes, renders every stage using verified Cycles Metal GPU, writes
fresh genuine 512/256 masters, feet review and rest comparison, audits, packs,
validates, and produces the round MP4. Source/script/master seals block stale
certification. The new GPU result remains pending; CPU output is labelled preview.

Commit attempt was blocked by sandbox denial of `.git/worktrees/lane-18/index.lock`.
Changes remain for the runner to commit with the requested co-author trailer.
`origin/master` is already an ancestor; no merge was needed. No push or PR.
