# Biplane — resumed round 2

**Candidate, not art-approved; no PASS marker.** The 256 px comparison is closer,
but still visibly different from the painting. At 64 px the unit reads correctly;
the wing, cockpit and strut proportions still distinguish the token.

## Changes and evidence

- Fitted full-depth wing, fuselage, cowling and tail geometry in the fixed source
  camera; shortened the actual propeller; rebuilt the curved solid support.
- Removed duplicate interplane struts and fitted four struts plus their solid end
  fittings to painted attachment points. Finished bevels/curves precede projection.
- Frozen camera UVs use densely sampled finished surfaces, one visibility BVH,
  camera-only painted pigment, existing generated unseen-surface fills, eight real
  AO/curvature bakes, product lighting and one frozen automatic histogram grade.
  The base retains physical cream shading with warmer top/darker rim pigment.
- Upper-wing ribs follow the wing during the crash. A corrected crash path keeps
  its widened tail in frame. Last two death samples and decoded frames are identical.
- All stage sheets, five animated WebPs, 256 px masters, top/front airborne gear
  review, decoded-atlas sheet, rest comparison and round-2 MP4 exist externally.
  Previous native CPU512 masters remain under `masters/biplane/round1-cpu/`;
  this round is **Cycles CPU, 256 px, 8 samples**. Fresh GPU512 masters are pending.

Measured silhouette IoU at alpha >127: **0.840495**, previous **0.678447**.
This metric does not establish painted richness or visual approval.

## Remaining visual gaps

At 256 px the struts are too thin, the cockpit/seat and cowling profile differ,
the lower wing retains some dark projected attachment marks, and the stone disc
is more uniformly shaded than the painting. The rotated crash tail/canvas exposes
simpler fills. Attack is restrained and its muzzle flashes are hard to read;
the support's keyed disappearance in death is still abrupt. These are reasons to
continue, not to issue PASS. At 64 px identity is clear, but parity is not reached.

The detail sheet enlarges 256 px CPU crops; it is not native 512 px evidence.
The five-clip MP4 is encoded from the actual decoded trimmed atlas, not raw PNGs.

## Exact checks

- Six provenance regression tests: **6 passed**.
- Geometry audit: finished UV error <0.003 px, camera-only pigment, exactly four
  interplane struts, all 40 poses inside the camera/above the ground, wheel axes
  aligned to flight, stationary disc, and held wreck: **passed**.
- Trimmed atlas: **1341 × 715, 177,884 bytes, quality 80**, 160 px logical cells,
  unchanged 8/8/10/4/10 frames. Lossless 8-bit alpha reconstructs exactly at all
  offsets; held death decodes identically. Q85 was 200,500 bytes, so Q80 is intentional.
- Video: **1600 × 348, H.264/yuv420p, 240 frames, 8.000 seconds**, ffprobe verified.
- Missing-input GPU shell preflight: failed as intended with stage/exit transcript.
  Regression checks reject CPU512 masquerading as GPU and stale GPU source hashes.
- Python syntax, both Bash scripts and `git diff --check`: passed.

No Rust, game rules or application UI changed; Rust/WASM/app test suites are not
applicable. The repository art gate and lead art review remain pending on the committed candidate.
The lead's GPU execution and visual/art review remain outstanding.

## Complete lead GPU pass

From this checkout, with no arguments:

```sh
ROUND=2 tools/art/anim3d/units/biplane/gpu.sh
```

The executable script verifies input/build hashes, rebuilds all five clips, audits
geometry, requires Cycles Metal GPU, renders every stage at native 512 px, exports
256 px masters, verifies every current source/render/grade hash, packs/validates the
160 px atlas and writes `biplane-round${ROUND}.mp4`. It defaults to 64 samples and
refuses final settings below 64. It retains `gpu-logs-biplane-r${ROUND}.log`,
`biplane-gpu-status.txt` and a round receipt; no GPU pass is inferred from CPU previews.
Neither this script nor technical checks create `biplane-PASS`.

Rebuild order is `prepare.py`, `render.sh build`, `render.sh register`,
`render.sh paint`, `render.sh animate`, then the GPU script. All `.blend` masters,
paintings/fills, bakes and raw/review evidence stay outside git. The candidate
atlas remains unwired; JSON rectangles and per-frame offsets require a trimmed
atlas reader. Do not sample it as the old fixed-cell grid.

Git could not create `.git/worktrees/lane-5/index.lock`, so changes remain
uncommitted for the runner. `origin/master` is already an ancestor of HEAD; no
merge is needed. No push, pull request or master merge was attempted.
